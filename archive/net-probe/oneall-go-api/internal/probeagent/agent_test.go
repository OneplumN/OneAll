package probeagent_test

import (
	"bytes"
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/gin-gonic/gin"
	"oneall-go-api/internal/config"
	"oneall-go-api/internal/httpapi"
	"oneall-go-api/internal/probeagent"
	"oneall-go-api/internal/store"
)

func TestAgentRunOnceClaimsExecutesAndReportsHTTPTask(t *testing.T) {
	gin.SetMode(gin.TestMode)
	apiRouter := gin.New()
	httpapi.RegisterRoutes(apiRouter, httpapi.RouterDependencies{Config: config.Config{}, Store: store.NewMemoryStore()})
	apiServer := httptest.NewServer(apiRouter)
	defer apiServer.Close()

	targetServer := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusNoContent)
	}))
	defer targetServer.Close()

	probe := requestJSON(t, apiServer.URL, http.MethodPost, "/api/v1/probes/register", map[string]any{
		"name":         "probe-agent-test",
		"region":       "上海",
		"network_type": "互联网",
		"capabilities": []string{"HTTP"},
	}, "OpsAdmin", http.StatusCreated)
	probeID := probe["id"].(string)
	token := probe["token"].(string)
	if probeID == "" || token == "" {
		t.Fatalf("probe id and token are required: %#v", probe)
	}

	task := requestJSON(t, apiServer.URL, http.MethodPost, "/api/v1/detection/one-off", map[string]any{
		"type":             "http",
		"protocol":         "HTTP",
		"target":           targetServer.URL,
		"probe":            probeID,
		"timeout_seconds":  2,
		"business_line":    "支付业务",
		"related_asset":    "api.oneall.internal",
		"environment":      "prod",
		"expected_status":  []int{204},
		"follow_redirects": true,
	}, "OpsEngineer", http.StatusCreated)
	taskID := task["id"].(string)

	agent, err := probeagent.New(probeagent.Config{
		BaseURL:      apiServer.URL,
		ProbeID:      probeID,
		Token:        token,
		Version:      "test",
		Capabilities: []string{"HTTP"},
		PollInterval: time.Second,
		Timeout:      2 * time.Second,
		TaskLimit:    1,
	})
	if err != nil {
		t.Fatal(err)
	}
	if err := agent.RunOnce(context.Background()); err != nil {
		t.Fatal(err)
	}

	detail := requestJSON(t, apiServer.URL, http.MethodGet, "/api/v1/detection/tasks/"+taskID, nil, "OpsAdmin", http.StatusOK)
	if detail["status"] != "success" {
		t.Fatalf("expected successful task, got %#v", detail)
	}
	if detail["completed_at"] == "" || detail["claimed_by_probe_id"] != probeID {
		t.Fatalf("expected claimed/completed task metadata, got %#v", detail)
	}
	result := detail["result"].(map[string]any)
	if result["status"] != "success" || result["status_code"].(float64) != 204 {
		t.Fatalf("unexpected probe result: %#v", result)
	}
}

func TestAgentSpoolsFailedResultAndFlushesOnNextRun(t *testing.T) {
	targetServer := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusNoContent)
	}))
	defer targetServer.Close()

	resultAttempts := 0
	claimCount := 0
	traceIDs := map[string]string{}
	apiServer := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("content-type", "application/json")
		if got := r.Header.Get("x-oneall-probe-id"); got != "PRB-test" {
			t.Errorf("expected probe id header, got %q", got)
		}
		if got := r.Header.Get("authorization"); got != "Bearer token" {
			t.Errorf("expected bearer token header, got %q", got)
		}
		if got := r.Header.Get("x-oneall-trace-id"); got == "" {
			t.Errorf("expected trace id header on %s", r.URL.Path)
		} else {
			traceIDs[r.URL.Path] = got
		}
		switch {
		case r.Method == http.MethodPost && r.URL.Path == "/api/v1/probes/nodes/PRB-test/heartbeat":
			_, _ = w.Write([]byte(`{"id":"PRB-test"}`))
		case r.Method == http.MethodPost && r.URL.Path == "/api/v1/probes/tasks/claim":
			claimCount++
			if claimCount == 1 {
				_, _ = w.Write([]byte(`{"items":[{"id":"DET-test","type":"http","protocol":"HTTP","target":"` + targetServer.URL + `","status":"running","timeout_seconds":2}]}`))
				return
			}
			_, _ = w.Write([]byte(`{"items":[]}`))
		case r.Method == http.MethodPost && r.URL.Path == "/api/v1/probes/tasks/DET-test/result":
			resultAttempts++
			if resultAttempts == 1 {
				http.Error(w, "temporary outage", http.StatusServiceUnavailable)
				return
			}
			_, _ = w.Write([]byte(`{"id":"DET-test","status":"success"}`))
		default:
			http.NotFound(w, r)
		}
	}))
	defer apiServer.Close()

	spoolPath := filepath.Join(t.TempDir(), "pending-results.json")
	agent, err := probeagent.New(probeagent.Config{
		BaseURL:   apiServer.URL,
		ProbeID:   "PRB-test",
		Token:     "token",
		Timeout:   2 * time.Second,
		TaskLimit: 1,
		SpoolPath: spoolPath,
	})
	if err != nil {
		t.Fatal(err)
	}
	if err := agent.RunOnce(context.Background()); err == nil {
		t.Fatal("expected first result submit to fail")
	}
	if _, err := os.Stat(spoolPath); err != nil {
		t.Fatalf("expected failed result to be spooled: %v", err)
	}
	if err := agent.RunOnce(context.Background()); err != nil {
		t.Fatal(err)
	}
	if _, err := os.Stat(spoolPath); !os.IsNotExist(err) {
		t.Fatalf("expected spool to be cleared, got %v", err)
	}
	if resultAttempts != 2 {
		t.Fatalf("expected result to be retried once, got %d attempts", resultAttempts)
	}
	for _, path := range []string{"/api/v1/probes/nodes/PRB-test/heartbeat", "/api/v1/probes/tasks/claim", "/api/v1/probes/tasks/DET-test/result"} {
		if traceIDs[path] == "" {
			t.Fatalf("expected trace id for %s", path)
		}
	}
}

func requestJSON(t *testing.T, baseURL string, method string, path string, body any, role string, expectedStatus int) map[string]any {
	t.Helper()
	var reader *bytes.Reader
	if body == nil {
		reader = bytes.NewReader(nil)
	} else {
		raw, _ := json.Marshal(body)
		reader = bytes.NewReader(raw)
	}
	request, err := http.NewRequest(method, baseURL+path, reader)
	if err != nil {
		t.Fatal(err)
	}
	request.Header.Set("content-type", "application/json")
	request.Header.Set("x-oneall-role", role)
	response, err := http.DefaultClient.Do(request)
	if err != nil {
		t.Fatal(err)
	}
	defer response.Body.Close()
	if response.StatusCode != expectedStatus {
		t.Fatalf("%s %s expected %d, got %d", method, path, expectedStatus, response.StatusCode)
	}
	var payload map[string]any
	if err := json.NewDecoder(response.Body).Decode(&payload); err != nil {
		t.Fatal(err)
	}
	return payload
}
