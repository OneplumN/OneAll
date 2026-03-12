package wss

import (
	"context"
	"crypto/tls"
	"errors"
	"fmt"
	"net/http"
	"net/url"
	"strings"
	"time"

	"github.com/gorilla/websocket"

	"github.com/one-pro/one-pro/probes/internal/api"
	"github.com/one-pro/one-pro/probes/internal/plugins/registry"
)

const headerPrefix = "header:"

// Probe validates WebSocket (WSS) connectivity and message exchange.
type Probe struct {
	timeout time.Duration
}

// New creates a WSS probe with the provided timeout.
func New(timeout time.Duration) *Probe {
	return &Probe{timeout: timeout}
}

// Register wires the WSS probe into the registry.
func Register(reg *registry.Registry, timeout time.Duration) {
	reg.Register(New(timeout))
}

// Protocols returns supported identifiers.
func (p *Probe) Protocols() []string {
	return []string{"WSS"}
}

// Execute performs the WebSocket handshake and optional send/receive.
func (p *Probe) Execute(ctx context.Context, task api.Task) (api.TaskResult, error) {
	target := strings.TrimSpace(task.Target)
	if target == "" {
		return api.TaskResult{Status: "failed", Message: "missing target"}, nil
	}
	endpoint, err := normalizeEndpoint(target)
	if err != nil {
		return api.TaskResult{Status: "failed", Message: err.Error()}, nil
	}
	meta := task.Metadata
	headers := buildHeaders(meta)
	if origin := metadataString(meta, "origin"); origin != "" {
		headers.Set("Origin", origin)
	}
	dialer := websocket.Dialer{
		HandshakeTimeout: p.timeout,
	}
	if metadataBool(meta, "insecure_skip_tls", false) {
		dialer.TLSClientConfig = &tls.Config{InsecureSkipVerify: true} // #nosec G402
	}
	if subproto := metadataString(meta, "subprotocol"); subproto != "" {
		dialer.Subprotocols = []string{subproto}
	}
	started := time.Now()
	conn, resp, err := dialer.DialContext(ctx, endpoint, headers)
	if err != nil {
		msg := err.Error()
		if resp != nil {
			msg = fmt.Sprintf("%s (status %d)", msg, resp.StatusCode)
		}
		return api.TaskResult{Status: "failed", Message: msg}, nil
	}
	defer conn.Close()
	payload := metadataString(meta, "payload")
	expect := metadataString(meta, "expect")
	waitForResponse := metadataBool(meta, "wait_for_response", expect != "")
	if payload != "" {
		_ = conn.SetWriteDeadline(time.Now().Add(p.timeout))
		if err := conn.WriteMessage(websocket.TextMessage, []byte(payload)); err != nil {
			return api.TaskResult{Status: "failed", Message: fmt.Sprintf("write failed: %v", err)}, nil
		}
		// 默认写入后等待响应，除非显式关闭
		if _, ok := meta["wait_for_response"]; !ok {
			waitForResponse = true
		}
	}
	var received string
	if waitForResponse {
		_ = conn.SetReadDeadline(time.Now().Add(p.timeout))
		_, msg, err := conn.ReadMessage()
		if err != nil {
			return api.TaskResult{Status: "failed", Message: fmt.Sprintf("read failed: %v", err)}, nil
		}
		received = string(msg)
	}
	latency := int(time.Since(started).Milliseconds())
	status := "success"
	message := ""
	if expect != "" && !strings.Contains(received, expect) {
		status = "failed"
		message = "响应不匹配期望内容"
	}
	result := api.TaskResult{
		Status:    status,
		Message:   message,
		LatencyMs: latency,
		Metadata: map[string]any{
			"wss": map[string]any{
				"endpoint":    endpoint,
				"payload":     payload,
				"response":    received,
				"expect":      expect,
				"wait":        waitForResponse,
				"subprotocol": metadataString(meta, "subprotocol"),
			},
		},
	}
	return result, nil
}

func normalizeEndpoint(raw string) (string, error) {
	value := strings.TrimSpace(raw)
	if value == "" {
		return "", errors.New("invalid target")
	}
	if !strings.Contains(value, "://") {
		value = "wss://" + value
	}
	parsed, err := url.Parse(value)
	if err != nil {
		return "", fmt.Errorf("invalid target: %w", err)
	}
	switch parsed.Scheme {
	case "http":
		parsed.Scheme = "ws"
	case "https":
		parsed.Scheme = "wss"
	}
	if parsed.Scheme != "ws" && parsed.Scheme != "wss" {
		return "", fmt.Errorf("unsupported scheme %s", parsed.Scheme)
	}
	if parsed.Host == "" {
		return "", errors.New("missing host")
	}
	return parsed.String(), nil
}

func buildHeaders(meta map[string]any) http.Header {
	headers := http.Header{}
	if meta == nil {
		return headers
	}
	for key := range meta {
		lower := strings.ToLower(key)
		if !strings.HasPrefix(lower, headerPrefix) {
			continue
		}
		name := strings.TrimSpace(key[len(headerPrefix):])
		if name == "" {
			continue
		}
		value := metadataString(meta, key)
		if value == "" {
			continue
		}
		headers.Set(name, value)
	}
	return headers
}

func metadataString(meta map[string]any, key string) string {
	if meta == nil {
		return ""
	}
	value, ok := meta[key]
	if !ok || value == nil {
		return ""
	}
	switch v := value.(type) {
	case string:
		return v
	case fmt.Stringer:
		return v.String()
	case []byte:
		return string(v)
	default:
		return fmt.Sprint(v)
	}
}

func metadataBool(meta map[string]any, key string, fallback bool) bool {
	if meta == nil {
		return fallback
	}
	value, ok := meta[key]
	if !ok || value == nil {
		return fallback
	}
	switch v := value.(type) {
	case bool:
		return v
	case string:
		lower := strings.ToLower(strings.TrimSpace(v))
		if lower == "true" || lower == "1" || lower == "yes" {
			return true
		}
		if lower == "false" || lower == "0" || lower == "no" {
			return false
		}
	}
	return fallback
}

