package api

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"
)

func TestClaimOneOffTaskReturnsTask(t *testing.T) {
	t.Parallel()

	scheduledAt := time.Now().UTC().Format(time.RFC3339Nano)
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/api/probes/tasks/claim" {
			t.Fatalf("unexpected path %s", r.URL.Path)
		}
		if got := r.Header.Get("Authorization"); got != "ProbeToken secret" {
			t.Fatalf("unexpected auth header %q", got)
		}
		_ = json.NewEncoder(w).Encode(map[string]any{
			"task_id":         "task-1",
			"target":          "https://example.com",
			"protocol":        "HTTPS",
			"timeout_seconds": 10,
			"expected_status": 200,
			"metadata":        map[string]any{"execution_source": "one_off"},
			"scheduled_at":    scheduledAt,
		})
	}))
	defer srv.Close()

	client, err := NewClient(srv.URL, "probe-1", "secret", 5*time.Second, false)
	if err != nil {
		t.Fatalf("new client: %v", err)
	}

	task, err := client.ClaimOneOffTask(context.Background(), 1)
	if err != nil {
		t.Fatalf("claim task: %v", err)
	}
	if task == nil || task.ID != "task-1" {
		t.Fatalf("unexpected task: %#v", task)
	}
	if task.ExpectStatus != 200 {
		t.Fatalf("unexpected expect status: %d", task.ExpectStatus)
	}
}

func TestSubmitOneOffResultPostsPayload(t *testing.T) {
	t.Parallel()

	posted := submitTaskResultRequest{}
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/api/probes/tasks/task-1/result" {
			t.Fatalf("unexpected path %s", r.URL.Path)
		}
		if err := json.NewDecoder(r.Body).Decode(&posted); err != nil {
			t.Fatalf("decode body: %v", err)
		}
		w.WriteHeader(http.StatusOK)
	}))
	defer srv.Close()

	client, err := NewClient(srv.URL, "probe-1", "secret", 5*time.Second, false)
	if err != nil {
		t.Fatalf("new client: %v", err)
	}

	err = client.SubmitOneOffResult(context.Background(), TaskResult{
		TaskID:     "task-1",
		Status:     "success",
		LatencyMs:  123,
		StatusCode: 200,
		Metadata:   map[string]any{"foo": "bar"},
		FinishedAt: time.Now().UTC(),
	})
	if err != nil {
		t.Fatalf("submit result: %v", err)
	}
	if posted.Status != "success" || posted.ResponseTimeMs != 123 || posted.StatusCode != 200 {
		t.Fatalf("unexpected payload: %#v", posted)
	}
}

func TestSubmitScheduleResultPostsPayload(t *testing.T) {
	t.Parallel()

	posted := submitScheduleResultRequest{}
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/api/probes/schedules/schedule-1/result" {
			t.Fatalf("unexpected path %s", r.URL.Path)
		}
		if err := json.NewDecoder(r.Body).Decode(&posted); err != nil {
			t.Fatalf("decode body: %v", err)
		}
		w.WriteHeader(http.StatusOK)
	}))
	defer srv.Close()

	client, err := NewClient(srv.URL, "probe-1", "secret", 5*time.Second, false)
	if err != nil {
		t.Fatalf("new client: %v", err)
	}

	scheduledAt := time.Now().UTC().Add(-time.Minute)
	finishedAt := time.Now().UTC()
	err = client.SubmitScheduleResult(context.Background(), TaskResult{
		TaskID:      "schedule-1-12345",
		ScheduleID:  "schedule-1",
		Status:      "timeout",
		Message:     "context deadline exceeded",
		LatencyMs:   5000,
		StatusCode:  504,
		Metadata:    map[string]any{"origin": "scheduler"},
		ScheduledAt: scheduledAt,
		FinishedAt:  finishedAt,
	})
	if err != nil {
		t.Fatalf("submit schedule result: %v", err)
	}
	if posted.ProbeID != "probe-1" {
		t.Fatalf("unexpected probe id: %q", posted.ProbeID)
	}
	if posted.ScheduledAt != scheduledAt.Format(time.RFC3339Nano) {
		t.Fatalf("unexpected scheduled_at: %q", posted.ScheduledAt)
	}
	if posted.Status != "timeout" || posted.ResponseTimeMs != 5000 || posted.StatusCode != 504 {
		t.Fatalf("unexpected payload: %#v", posted)
	}
}
