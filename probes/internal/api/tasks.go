package api

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"time"
)

type claimTaskRequest struct {
	ProbeID string `json:"probe_id"`
	Limit   int    `json:"limit,omitempty"`
}

type claimTaskResponse struct {
	TaskID         string         `json:"task_id"`
	Target         string         `json:"target"`
	Protocol       string         `json:"protocol"`
	TimeoutSeconds int            `json:"timeout_seconds"`
	ExpectedStatus int            `json:"expected_status"`
	Metadata       map[string]any `json:"metadata"`
	ScheduledAt    string         `json:"scheduled_at"`
}

type submitTaskResultRequest struct {
	Status         string         `json:"status"`
	Message        string         `json:"message,omitempty"`
	ResponseTimeMs int            `json:"response_time_ms,omitempty"`
	StatusCode     int            `json:"status_code,omitempty"`
	Metadata       map[string]any `json:"metadata,omitempty"`
	FinishedAt     string         `json:"finished_at,omitempty"`
}

type submitScheduleResultRequest struct {
	ProbeID        string         `json:"probe_id"`
	ScheduledAt    string         `json:"scheduled_at"`
	Status         string         `json:"status"`
	Message        string         `json:"message,omitempty"`
	ResponseTimeMs int            `json:"response_time_ms,omitempty"`
	StatusCode     int            `json:"status_code,omitempty"`
	Metadata       map[string]any `json:"metadata,omitempty"`
	FinishedAt     string         `json:"finished_at,omitempty"`
}

func (c *Client) ClaimOneOffTask(ctx context.Context, limit int) (*Task, error) {
	body, err := json.Marshal(claimTaskRequest{
		ProbeID: c.nodeID,
		Limit:   limit,
	})
	if err != nil {
		return nil, fmt.Errorf("encode claim request: %w", err)
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodPost, c.endpoint("api", "probes", "tasks", "claim"), bytes.NewReader(body))
	if err != nil {
		return nil, err
	}
	req.Header.Set("Content-Type", "application/json")
	c.applyAuth(req)
	c.applySecurity(req, body)

	resp, err := c.http.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusNoContent {
		return nil, nil
	}
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("claim task: unexpected status %d", resp.StatusCode)
	}

	var payload claimTaskResponse
	if err := json.NewDecoder(resp.Body).Decode(&payload); err != nil {
		return nil, fmt.Errorf("decode claim response: %w", err)
	}

	task := &Task{
		ID:             payload.TaskID,
		Target:         payload.Target,
		Protocol:       payload.Protocol,
		TimeoutSeconds: payload.TimeoutSeconds,
		ExpectStatus:   payload.ExpectedStatus,
		Metadata:       payload.Metadata,
	}
	if payload.ScheduledAt != "" {
		scheduledAt, err := time.Parse(time.RFC3339Nano, payload.ScheduledAt)
		if err == nil {
			task.ScheduledAt = scheduledAt
		}
	}
	return task, nil
}

func (c *Client) SubmitOneOffResult(ctx context.Context, result TaskResult) error {
	payload := submitTaskResultRequest{
		Status:         result.Status,
		Message:        result.Message,
		ResponseTimeMs: result.LatencyMs,
		StatusCode:     result.StatusCode,
		Metadata:       result.Metadata,
	}
	if !result.FinishedAt.IsZero() {
		payload.FinishedAt = result.FinishedAt.Format(time.RFC3339Nano)
	}

	body, err := json.Marshal(payload)
	if err != nil {
		return fmt.Errorf("encode result request: %w", err)
	}

	req, err := http.NewRequestWithContext(
		ctx,
		http.MethodPost,
		c.endpoint("api", "probes", "tasks", result.TaskID, "result"),
		bytes.NewReader(body),
	)
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")
	c.applyAuth(req)
	c.applySecurity(req, body)

	resp, err := c.http.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("submit result: unexpected status %d", resp.StatusCode)
	}
	return nil
}

func (c *Client) SubmitScheduleResult(ctx context.Context, result TaskResult) error {
	if result.ScheduleID == "" {
		return fmt.Errorf("submit schedule result: missing schedule id")
	}
	if result.ScheduledAt.IsZero() {
		return fmt.Errorf("submit schedule result: missing scheduled_at")
	}

	payload := submitScheduleResultRequest{
		ProbeID:        c.nodeID,
		ScheduledAt:    result.ScheduledAt.Format(time.RFC3339Nano),
		Status:         result.Status,
		Message:        result.Message,
		ResponseTimeMs: result.LatencyMs,
		StatusCode:     result.StatusCode,
		Metadata:       result.Metadata,
	}
	if !result.FinishedAt.IsZero() {
		payload.FinishedAt = result.FinishedAt.Format(time.RFC3339Nano)
	}

	body, err := json.Marshal(payload)
	if err != nil {
		return fmt.Errorf("encode schedule result request: %w", err)
	}

	req, err := http.NewRequestWithContext(
		ctx,
		http.MethodPost,
		c.endpoint("api", "probes", "schedules", result.ScheduleID, "result"),
		bytes.NewReader(body),
	)
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")
	c.applyAuth(req)
	c.applySecurity(req, body)

	resp, err := c.http.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("submit schedule result: unexpected status %d", resp.StatusCode)
	}
	return nil
}
