package http

import (
	"context"
	"fmt"
	"io"
	"net"
	"net/http"
	"net/url"
	"strings"
	"time"

	"github.com/one-pro/one-pro/probes/internal/api"
	"github.com/one-pro/one-pro/probes/internal/plugins/registry"
)

// Probe implements HTTP/HTTPS style checks.
type Probe struct {
	client *http.Client
}

// New creates a Probe with the desired timeout.
func New(timeout time.Duration) *Probe {
	return &Probe{
		client: &http.Client{Timeout: timeout},
	}
}

// Protocols returns the supported protocol identifiers.
func (p *Probe) Protocols() []string {
	return []string{"HTTP", "HTTPS"}
}

// Execute performs the HTTP call described by the task.
func (p *Probe) Execute(ctx context.Context, task api.Task) (api.TaskResult, error) {
	target := task.Target
	if target == "" {
		return api.TaskResult{Status: "failed", Message: "missing target"}, nil
	}
	if err := ValidateURL(target); err != nil {
		return api.TaskResult{Status: "failed", Message: err.Error()}, nil
	}
	req, err := p.buildRequest(ctx, task)
	if err != nil {
		return api.TaskResult{Status: "failed", Message: err.Error()}, nil
	}
	started := time.Now()
	resp, err := p.client.Do(req)
	if err != nil {
		return api.TaskResult{Status: "failed", Message: err.Error()}, nil
	}
	defer resp.Body.Close()
	status := "success"
	if task.ExpectStatus != 0 && resp.StatusCode != task.ExpectStatus {
		status = "failed"
	}
	return api.TaskResult{
		Protocol:   task.Protocol,
		Status:     status,
		StatusCode: resp.StatusCode,
		LatencyMs:  int(time.Since(started).Milliseconds()),
	}, nil
}

// Register wires the probe into the registry.
func Register(reg *registry.Registry, timeout time.Duration) {
	reg.Register(New(timeout))
}

const headerPrefix = "header:"

func (p *Probe) buildRequest(ctx context.Context, task api.Task) (*http.Request, error) {
	method := strings.ToUpper(strings.TrimSpace(metadataValue(task, "method")))
	if method == "" {
		method = http.MethodGet
	}
	var body io.Reader
	if payload := metadataValue(task, "body"); payload != "" {
		body = strings.NewReader(payload)
	}
	req, err := http.NewRequestWithContext(ctx, method, task.Target, body)
	if err != nil {
		return nil, err
	}
	for key := range task.Metadata {
		if !strings.HasPrefix(strings.ToLower(key), headerPrefix) {
			continue
		}
		headerName := strings.TrimSpace(key[len(headerPrefix):])
		if headerName == "" {
			continue
		}
		value := metadataValue(task, key)
		if value == "" {
			continue
		}
		req.Header.Set(headerName, value)
	}
	return req, nil
}

func metadataValue(task api.Task, key string) string {
	if task.Metadata == nil {
		return ""
	}
	value, ok := task.Metadata[key]
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

// ValidateURL ensures target is a valid URL.
func ValidateURL(raw string) error {
	parsed, err := url.Parse(raw)
	if err != nil {
		return err
	}
	if parsed.Scheme == "" || parsed.Host == "" {
		return fmt.Errorf("invalid target: %s", raw)
	}
	host := parsed.Hostname()
	if host == "" {
		return fmt.Errorf("invalid host")
	}
	if net.ParseIP(host) == nil && parsed.Hostname() == "" {
		return fmt.Errorf("unresolvable host")
	}
	return nil
}
