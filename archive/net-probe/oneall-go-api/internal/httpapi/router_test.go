package httpapi

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/gin-gonic/gin"
	"oneall-go-api/internal/config"
	"oneall-go-api/internal/store"
)

func TestProbeLifecycleAPI(t *testing.T) {
	gin.SetMode(gin.TestMode)
	memory := store.NewMemoryStore()
	router := gin.New()
	RegisterRoutes(router, RouterDependencies{Config: config.Config{}, Store: memory})

	probe := requestJSON(t, router, http.MethodPost, "/api/v1/probes/register", map[string]any{
		"name":         "probe-test-01",
		"region":       "上海",
		"network_type": "互联网",
		"ip_address":   "10.10.9.9",
		"capabilities": []string{"HTTP", "DNS"},
	}, "OpsAdmin", http.StatusCreated)
	probeID := probe["id"].(string)
	token := probe["token"].(string)
	if token == "" {
		t.Fatalf("probe token must be returned once on registration: %#v", probe)
	}
	probes := requestJSON(t, router, http.MethodGet, "/api/v1/probes/nodes", nil, "OpsAdmin", http.StatusOK)
	listed := probes["items"].([]any)[0].(map[string]any)
	if listed["token"] != nil && listed["token"] != "" {
		t.Fatalf("probe token must not be returned in list payload: %#v", listed)
	}

	task := requestJSON(t, router, http.MethodPost, "/api/v1/detection/one-off", map[string]any{
		"type":   "http",
		"target": "https://api.oneall.internal/health",
		"probe":  "probe-test-01",
	}, "OpsEngineer", http.StatusCreated)
	taskID := task["id"].(string)

	claimed := requestJSON(t, router, http.MethodPost, "/api/v1/probes/tasks/claim", map[string]any{
		"probe_id": probeID,
		"limit":    1,
	}, "OpsAdmin", http.StatusOK)
	items := claimed["items"].([]any)
	if len(items) != 1 {
		t.Fatalf("expected one claimed task, got %d", len(items))
	}
	first := items[0].(map[string]any)
	if first["id"] != taskID || first["status"] != "running" || first["claimed_by_probe_id"] != probeID {
		t.Fatalf("unexpected claimed task payload: %#v", first)
	}

	claimedAgain := requestJSON(t, router, http.MethodPost, "/api/v1/probes/tasks/claim", map[string]any{
		"probe_id": probeID,
		"limit":    1,
	}, "OpsAdmin", http.StatusOK)
	if len(claimedAgain["items"].([]any)) != 0 {
		t.Fatalf("running task should not be claimed twice: %#v", claimedAgain)
	}

	heartbeat := performRequestWithHeaders(router, http.MethodPost, "/api/v1/probes/nodes/"+probeID+"/heartbeat", map[string]any{
		"version":      "test",
		"capabilities": []string{"HTTP", "DNS"},
	}, "OpsAdmin", map[string]string{
		"authorization":       "Bearer " + token,
		"x-oneall-probe-id":   probeID,
		"x-oneall-role":       "",
		"content-type":        "application/json",
		"x-oneall-test-trace": "heartbeat",
	})
	if heartbeat.Code != http.StatusOK {
		t.Fatalf("expected heartbeat accepted, got %d: %s", heartbeat.Code, heartbeat.Body.String())
	}

	invalidHeartbeat := performRequestWithHeaders(router, http.MethodPost, "/api/v1/probes/nodes/"+probeID+"/heartbeat", map[string]any{
		"version": "test",
	}, "OpsAdmin", map[string]string{
		"authorization":     "Bearer invalid",
		"x-oneall-probe-id": probeID,
	})
	if invalidHeartbeat.Code != http.StatusUnauthorized {
		t.Fatalf("expected invalid heartbeat rejected, got %d: %s", invalidHeartbeat.Code, invalidHeartbeat.Body.String())
	}

	result := requestJSON(t, router, http.MethodPost, "/api/v1/probes/tasks/"+taskID+"/result", map[string]any{
		"probe_id":          probeID,
		"result_id":         probeID + ":" + taskID,
		"status":            "failed",
		"response_time_ms":  5018,
		"status_code":       "504",
		"message":           "HTTP 请求超时",
		"diagnostic_detail": "timeout",
	}, "OpsAdmin", http.StatusOK)
	if result["status"] != "failed" || result["completed_at"] == "" || result["latency_ms"].(float64) != 5018 {
		t.Fatalf("unexpected result payload: %#v", result)
	}
	duplicateResult := requestJSON(t, router, http.MethodPost, "/api/v1/probes/tasks/"+taskID+"/result", map[string]any{
		"probe_id":         probeID,
		"result_id":        probeID + ":" + taskID,
		"status":           "failed",
		"response_time_ms": 5018,
		"message":          "重复回传",
	}, "OpsAdmin", http.StatusOK)
	if duplicateResult["message"] == "重复回传" {
		t.Fatalf("duplicate result should return existing final task, got %#v", duplicateResult)
	}
	alerts := requestJSON(t, router, http.MethodGet, "/api/v1/alerts/events", nil, "OpsAdmin", http.StatusOK)
	createdForTask := 0
	for _, item := range alerts["items"].([]any) {
		alert := item.(map[string]any)
		if alert["sourceTaskId"] == taskID {
			createdForTask++
		}
	}
	if createdForTask != 1 {
		t.Fatalf("duplicate result should not create duplicate alerts: %#v", alerts)
	}

	runtime := requestJSON(t, router, http.MethodGet, "/api/v1/probes/nodes/"+probeID+"/runtime", nil, "OpsAdmin", http.StatusOK)
	if runtime["probe_id"] != probeID {
		t.Fatalf("unexpected runtime payload: %#v", runtime)
	}

	versions := requestJSON(t, router, http.MethodGet, "/api/v1/probes/nodes/"+probeID+"/config/versions", nil, "OpsAdmin", http.StatusOK)
	if len(versions["items"].([]any)) == 0 {
		t.Fatalf("expected config versions, got %#v", versions)
	}
}

func TestProbeRegisterValidation(t *testing.T) {
	gin.SetMode(gin.TestMode)
	router := gin.New()
	RegisterRoutes(router, RouterDependencies{Config: config.Config{}, Store: store.NewMemoryStore()})

	response := performRequest(router, http.MethodPost, "/api/v1/probes/register", map[string]any{
		"name": "probe-missing-region",
	}, "OpsAdmin")
	if response.Code != http.StatusBadRequest {
		t.Fatalf("expected 400, got %d: %s", response.Code, response.Body.String())
	}
}

func requestJSON(t *testing.T, router http.Handler, method string, path string, body any, role string, expectedStatus int) map[string]any {
	t.Helper()
	response := performRequest(router, method, path, body, role)
	if response.Code != expectedStatus {
		t.Fatalf("%s %s expected %d, got %d: %s", method, path, expectedStatus, response.Code, response.Body.String())
	}
	if response.Body.Len() == 0 {
		return map[string]any{}
	}
	var payload map[string]any
	if err := json.Unmarshal(response.Body.Bytes(), &payload); err != nil {
		t.Fatalf("invalid JSON response: %v\n%s", err, response.Body.String())
	}
	return payload
}

func performRequest(router http.Handler, method string, path string, body any, role string) *httptest.ResponseRecorder {
	return performRequestWithHeaders(router, method, path, body, role, nil)
}

func performRequestWithHeaders(router http.Handler, method string, path string, body any, role string, headers map[string]string) *httptest.ResponseRecorder {
	var reader *bytes.Reader
	if body == nil {
		reader = bytes.NewReader(nil)
	} else {
		raw, _ := json.Marshal(body)
		reader = bytes.NewReader(raw)
	}
	request := httptest.NewRequest(method, path, reader)
	if body != nil {
		request.Header.Set("content-type", "application/json")
	}
	if role != "" {
		request.Header.Set("x-oneall-role", role)
	}
	for key, value := range headers {
		if value == "" {
			request.Header.Del(key)
			continue
		}
		request.Header.Set(key, value)
	}
	response := httptest.NewRecorder()
	router.ServeHTTP(response, request)
	return response
}
