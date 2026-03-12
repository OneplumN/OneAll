package tcp

import (
	"bufio"
	"context"
	"errors"
	"fmt"
	"net"
	"strconv"
	"strings"
	"time"

	"github.com/one-pro/one-pro/probes/internal/api"
	"github.com/one-pro/one-pro/probes/internal/plugins/registry"
)

// Probe executes simple TCP/Telnet-style connectivity checks.
type Probe struct {
	timeout time.Duration
}

// New creates a TCP probe with the given timeout.
func New(timeout time.Duration) *Probe {
	return &Probe{timeout: timeout}
}

// Register makes the probe available for TCP/Telnet protocols.
func Register(reg *registry.Registry, timeout time.Duration) {
	reg.Register(New(timeout))
}

// Protocols advertises supported protocols.
func (p *Probe) Protocols() []string {
	return []string{"TCP", "Telnet"}
}

// Execute performs the connectivity check using task metadata.
func (p *Probe) Execute(ctx context.Context, task api.Task) (api.TaskResult, error) {
	host, port, err := parseTarget(task.Target, task.Metadata)
	if err != nil {
		return api.TaskResult{Status: "failed", Message: err.Error()}, nil
	}
	payload := metadataString(task.Metadata, "payload")
	expect := metadataString(task.Metadata, "expect")
	maxRead := metadataInt(task.Metadata, "max_read_bytes", 512)
	started := time.Now()
	addr := net.JoinHostPort(host, port)
	conn, err := dialContext(ctx, addr, p.timeout)
	if err != nil {
		return api.TaskResult{Status: "failed", Message: err.Error()}, nil
	}
	defer conn.Close()
	_ = conn.SetDeadline(time.Now().Add(p.timeout))
	var banner string
	if payload != "" {
		if _, err := conn.Write([]byte(payload)); err != nil {
			return api.TaskResult{Status: "failed", Message: fmt.Sprintf("write failed: %v", err)}, nil
		}
	}
	if maxRead > 0 {
		reader := bufio.NewReader(conn)
		buf := make([]byte, maxRead)
		n, _ := reader.Read(buf)
		if n > 0 {
			banner = string(buf[:n])
		}
	}
	status := "success"
	message := ""
	if expect != "" && !strings.Contains(banner, expect) {
		status = "failed"
		message = "响应不包含期望内容"
	}
	return api.TaskResult{
		Status:    status,
		Message:   message,
		LatencyMs: int(time.Since(started).Milliseconds()),
		Metadata: map[string]any{
			"tcp": map[string]any{
				"banner":    banner,
				"payload":   payload,
				"expect":    expect,
				"max_read":  maxRead,
				"remote":    addr,
			},
		},
	}, nil
}

func parseTarget(target string, meta map[string]any) (string, string, error) {
	if target == "" {
		return "", "", errors.New("missing target")
	}
	parts := strings.Split(target, ":")
	host := strings.TrimSpace(parts[0])
	if host == "" {
		return "", "", errors.New("invalid host")
	}
	port := metadataString(meta, "port")
	if port == "" && len(parts) > 1 {
		port = parts[1]
	}
	if port == "" {
		port = "23"
	}
	if _, err := strconv.Atoi(port); err != nil {
		return "", "", fmt.Errorf("invalid port %s", port)
	}
	return host, port, nil
}

func dialContext(ctx context.Context, addr string, timeout time.Duration) (net.Conn, error) {
	dialer := &net.Dialer{Timeout: timeout}
	return dialer.DialContext(ctx, "tcp", addr)
}

func metadataString(meta map[string]any, key string) string {
	if meta == nil {
		return ""
	}
	if value, ok := meta[key]; ok {
		switch v := value.(type) {
		case string:
			return v
		case fmt.Stringer:
			return v.String()
		case []byte:
			return string(v)
		}
	}
	return ""
}

func metadataInt(meta map[string]any, key string, fallback int) int {
	if meta == nil {
		return fallback
	}
	if value, ok := meta[key]; ok {
		switch v := value.(type) {
		case int:
			return v
		case int32:
			return int(v)
		case int64:
			return int(v)
		case float32:
			return int(v)
		case float64:
			return int(v)
		case string:
			if parsed, err := strconv.Atoi(strings.TrimSpace(v)); err == nil {
				return parsed
			}
		}
	}
	return fallback
}
