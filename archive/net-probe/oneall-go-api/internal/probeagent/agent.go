package probeagent

import (
	"bytes"
	"context"
	"crypto/rand"
	"crypto/tls"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net"
	"net/http"
	"net/url"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"time"

	"oneall-go-api/internal/domain"
)

type Config struct {
	BaseURL      string
	ProbeID      string
	Token        string
	Version      string
	Capabilities []string
	PollInterval time.Duration
	Timeout      time.Duration
	TaskLimit    int
	SpoolPath    string
}

type Agent struct {
	config Config
	client *http.Client
}

type pendingResult struct {
	TaskID string         `json:"task_id"`
	Result map[string]any `json:"result"`
}

func New(config Config) (*Agent, error) {
	config.BaseURL = strings.TrimRight(valueOrDefault(config.BaseURL, "http://127.0.0.1:5184"), "/")
	config.Version = valueOrDefault(config.Version, "dev")
	if len(config.Capabilities) == 0 {
		config.Capabilities = []string{"HTTP", "HTTPS", "TCP", "DNS", "CERTIFICATE"}
	}
	if config.PollInterval <= 0 {
		config.PollInterval = 5 * time.Second
	}
	if config.Timeout <= 0 {
		config.Timeout = 10 * time.Second
	}
	if config.TaskLimit <= 0 {
		config.TaskLimit = 5
	}
	if config.TaskLimit > 10 {
		config.TaskLimit = 10
	}
	if config.ProbeID == "" {
		return nil, errors.New("probe id is required")
	}
	if config.Token == "" {
		return nil, errors.New("probe token is required")
	}
	if config.SpoolPath == "" {
		config.SpoolPath = defaultSpoolPath(config.ProbeID)
	}
	return &Agent{
		config: config,
		client: &http.Client{Timeout: config.Timeout + 2*time.Second},
	}, nil
}

func ConfigFromEnv() Config {
	return Config{
		BaseURL:      os.Getenv("ONEALL_API_BASE"),
		ProbeID:      os.Getenv("ONEALL_PROBE_ID"),
		Token:        os.Getenv("ONEALL_PROBE_TOKEN"),
		Version:      os.Getenv("ONEALL_PROBE_VERSION"),
		Capabilities: splitCSV(os.Getenv("ONEALL_PROBE_CAPABILITIES")),
		PollInterval: durationEnv("ONEALL_PROBE_POLL_INTERVAL", 5*time.Second),
		Timeout:      durationEnv("ONEALL_PROBE_TIMEOUT", 10*time.Second),
		TaskLimit:    intEnv("ONEALL_PROBE_TASK_LIMIT", 5),
		SpoolPath:    os.Getenv("ONEALL_PROBE_SPOOL_PATH"),
	}
}

func (a *Agent) Run(ctx context.Context) error {
	backoff := a.config.PollInterval
	for {
		if err := a.RunOnce(ctx); err != nil && ctx.Err() == nil {
			fmt.Fprintf(os.Stderr, "oneall probe agent: %v\n", err)
			backoff = nextBackoff(backoff, 2*time.Minute)
		} else {
			backoff = a.config.PollInterval
		}
		select {
		case <-ctx.Done():
			return ctx.Err()
		case <-time.After(backoff):
		}
	}
}

func (a *Agent) RunOnce(ctx context.Context) error {
	if err := a.heartbeat(ctx); err != nil {
		return err
	}
	if err := a.flushPendingResults(ctx); err != nil {
		return err
	}
	tasks, err := a.claimTasks(ctx)
	if err != nil {
		return err
	}
	for _, task := range tasks {
		result := a.execute(ctx, task)
		if err := a.submitResult(ctx, task.ID, result); err != nil {
			if storeErr := a.storePendingResult(task.ID, result); storeErr != nil {
				return fmt.Errorf("%w; failed to spool result: %v", err, storeErr)
			}
			return err
		}
	}
	return nil
}

func (a *Agent) heartbeat(ctx context.Context) error {
	body := map[string]any{
		"version":      a.config.Version,
		"capabilities": a.config.Capabilities,
	}
	return a.post(ctx, fmt.Sprintf("/api/v1/probes/nodes/%s/heartbeat", url.PathEscape(a.config.ProbeID)), body, nil)
}

func (a *Agent) claimTasks(ctx context.Context) ([]domain.DetectionTask, error) {
	var response struct {
		Items []domain.DetectionTask `json:"items"`
	}
	err := a.post(ctx, "/api/v1/probes/tasks/claim", map[string]any{
		"probe_id": a.config.ProbeID,
		"limit":    a.config.TaskLimit,
	}, &response)
	return response.Items, err
}

func (a *Agent) submitResult(ctx context.Context, taskID string, result map[string]any) error {
	return a.post(ctx, fmt.Sprintf("/api/v1/probes/tasks/%s/result", url.PathEscape(taskID)), result, nil)
}

func (a *Agent) post(ctx context.Context, path string, body any, output any) error {
	raw, err := json.Marshal(body)
	if err != nil {
		return err
	}
	request, err := http.NewRequestWithContext(ctx, http.MethodPost, a.config.BaseURL+path, bytes.NewReader(raw))
	if err != nil {
		return err
	}
	request.Header.Set("content-type", "application/json")
	request.Header.Set("authorization", "Bearer "+a.config.Token)
	request.Header.Set("x-oneall-probe-id", a.config.ProbeID)
	request.Header.Set("x-oneall-trace-id", newTraceID())
	response, err := a.client.Do(request)
	if err != nil {
		return err
	}
	defer response.Body.Close()
	if response.StatusCode >= 300 {
		rawBody, _ := io.ReadAll(io.LimitReader(response.Body, 4096))
		return fmt.Errorf("%s %s failed: %s", request.Method, path, strings.TrimSpace(string(rawBody)))
	}
	if output == nil {
		return nil
	}
	return json.NewDecoder(response.Body).Decode(output)
}

func (a *Agent) flushPendingResults(ctx context.Context) error {
	items, err := a.loadPendingResults()
	if err != nil {
		return err
	}
	if len(items) == 0 {
		return nil
	}
	remaining := make([]pendingResult, 0, len(items))
	for _, item := range items {
		if err := a.submitResult(ctx, item.TaskID, item.Result); err != nil {
			remaining = append(remaining, item)
		}
	}
	return a.savePendingResults(remaining)
}

func (a *Agent) storePendingResult(taskID string, result map[string]any) error {
	items, err := a.loadPendingResults()
	if err != nil {
		return err
	}
	resultID, _ := result["result_id"].(string)
	for index, item := range items {
		itemResultID, _ := item.Result["result_id"].(string)
		if item.TaskID == taskID || (resultID != "" && itemResultID == resultID) {
			items[index] = pendingResult{TaskID: taskID, Result: result}
			return a.savePendingResults(items)
		}
	}
	items = append(items, pendingResult{TaskID: taskID, Result: result})
	return a.savePendingResults(items)
}

func (a *Agent) loadPendingResults() ([]pendingResult, error) {
	raw, err := os.ReadFile(a.config.SpoolPath)
	if errors.Is(err, os.ErrNotExist) {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	if len(bytes.TrimSpace(raw)) == 0 {
		return nil, nil
	}
	var items []pendingResult
	if err := json.Unmarshal(raw, &items); err != nil {
		return nil, err
	}
	return items, nil
}

func (a *Agent) savePendingResults(items []pendingResult) error {
	if err := os.MkdirAll(filepath.Dir(a.config.SpoolPath), 0o755); err != nil {
		return err
	}
	if len(items) == 0 {
		if err := os.Remove(a.config.SpoolPath); err != nil && !errors.Is(err, os.ErrNotExist) {
			return err
		}
		return nil
	}
	raw, err := json.MarshalIndent(items, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(a.config.SpoolPath, raw, 0o600)
}

func (a *Agent) execute(ctx context.Context, task domain.DetectionTask) map[string]any {
	start := time.Now()
	timeout := a.config.Timeout
	if task.TimeoutSec > 0 {
		timeout = time.Duration(task.TimeoutSec) * time.Second
	}
	runCtx, cancel := context.WithTimeout(ctx, timeout)
	defer cancel()

	result := map[string]any{
		"probe_id":  a.config.ProbeID,
		"task_id":   task.ID,
		"result_id": fmt.Sprintf("%s:%s", a.config.ProbeID, task.ID),
		"status":    "failed",
		"success":   false,
	}
	statusCode, message, err := a.executeByType(runCtx, task)
	latencyMs := int(time.Since(start).Milliseconds())
	result["latency_ms"] = latencyMs
	result["response_time_ms"] = latencyMs
	if statusCode > 0 {
		result["status_code"] = statusCode
	}
	if err != nil {
		result["message"] = err.Error()
		return result
	}
	result["status"] = "success"
	result["success"] = true
	result["message"] = message
	return result
}

func (a *Agent) executeByType(ctx context.Context, task domain.DetectionTask) (int, string, error) {
	protocol := strings.ToUpper(valueOrDefault(task.Protocol, task.Type))
	switch protocol {
	case "HTTP", "HTTPS":
		return a.executeHTTP(ctx, task)
	case "TCP", "TELNET":
		return 0, "TCP 连接成功", executeTCP(ctx, task)
	case "DNS":
		return 0, "DNS 解析成功", executeDNS(ctx, task)
	case "CERT", "CERTIFICATE":
		return 0, "证书检查成功", executeCertificate(ctx, task)
	default:
		return 0, "", fmt.Errorf("unsupported probe task protocol: %s", protocol)
	}
}

func (a *Agent) executeHTTP(ctx context.Context, task domain.DetectionTask) (int, string, error) {
	target := task.Target
	if !strings.HasPrefix(target, "http://") && !strings.HasPrefix(target, "https://") {
		scheme := strings.ToLower(valueOrDefault(task.Protocol, "http"))
		target = scheme + "://" + target
	}
	request, err := http.NewRequestWithContext(ctx, http.MethodGet, target, nil)
	if err != nil {
		return 0, "", err
	}
	response, err := a.client.Do(request)
	if err != nil {
		return 0, "", err
	}
	defer response.Body.Close()
	_, _ = io.Copy(io.Discard, io.LimitReader(response.Body, 4096))
	if response.StatusCode < 200 || response.StatusCode >= 400 {
		return response.StatusCode, "", fmt.Errorf("HTTP 状态码异常：%d", response.StatusCode)
	}
	return response.StatusCode, "HTTP 请求成功", nil
}

func executeTCP(ctx context.Context, task domain.DetectionTask) error {
	address, err := hostPort(task, 80)
	if err != nil {
		return err
	}
	var dialer net.Dialer
	conn, err := dialer.DialContext(ctx, "tcp", address)
	if err != nil {
		return err
	}
	return conn.Close()
}

func executeDNS(ctx context.Context, task domain.DetectionTask) error {
	host, err := hostOnly(task.Target)
	if err != nil {
		return err
	}
	records, err := net.DefaultResolver.LookupHost(ctx, host)
	if err != nil {
		return err
	}
	if len(records) == 0 {
		return errors.New("DNS 未返回记录")
	}
	return nil
}

func executeCertificate(ctx context.Context, task domain.DetectionTask) error {
	address, err := hostPort(task, 443)
	if err != nil {
		return err
	}
	dialer := &net.Dialer{}
	conn, err := tls.DialWithDialer(dialer, "tcp", address, &tls.Config{ServerName: strings.Split(address, ":")[0]})
	if err != nil {
		return err
	}
	defer conn.Close()
	if len(conn.ConnectionState().PeerCertificates) == 0 {
		return errors.New("未获取到证书")
	}
	if time.Now().After(conn.ConnectionState().PeerCertificates[0].NotAfter) {
		return errors.New("证书已过期")
	}
	return nil
}

func hostPort(task domain.DetectionTask, defaultPort int) (string, error) {
	host, port, err := net.SplitHostPort(task.Target)
	if err == nil {
		return net.JoinHostPort(host, port), nil
	}
	parsed, parseErr := url.Parse(task.Target)
	if parseErr == nil && parsed.Host != "" {
		host = parsed.Hostname()
		if parsed.Port() != "" {
			port = parsed.Port()
		}
	}
	if host == "" {
		host = strings.TrimPrefix(strings.TrimPrefix(task.Target, "http://"), "https://")
		host = strings.Split(host, "/")[0]
	}
	if task.Port > 0 {
		port = strconv.Itoa(task.Port)
	}
	if port == "" {
		port = strconv.Itoa(defaultPort)
	}
	if host == "" {
		return "", errors.New("target host is required")
	}
	return net.JoinHostPort(host, port), nil
}

func hostOnly(target string) (string, error) {
	if parsed, err := url.Parse(target); err == nil && parsed.Hostname() != "" {
		return parsed.Hostname(), nil
	}
	host := strings.Split(strings.TrimPrefix(strings.TrimPrefix(target, "http://"), "https://"), "/")[0]
	host = strings.Split(host, ":")[0]
	if host == "" {
		return "", errors.New("target host is required")
	}
	return host, nil
}

func splitCSV(value string) []string {
	if value == "" {
		return nil
	}
	parts := strings.Split(value, ",")
	items := make([]string, 0, len(parts))
	for _, part := range parts {
		part = strings.TrimSpace(part)
		if part != "" {
			items = append(items, strings.ToUpper(part))
		}
	}
	return items
}

func durationEnv(key string, fallback time.Duration) time.Duration {
	value := os.Getenv(key)
	if value == "" {
		return fallback
	}
	duration, err := time.ParseDuration(value)
	if err != nil {
		return fallback
	}
	return duration
}

func intEnv(key string, fallback int) int {
	value := os.Getenv(key)
	if value == "" {
		return fallback
	}
	number, err := strconv.Atoi(value)
	if err != nil {
		return fallback
	}
	return number
}

func defaultSpoolPath(probeID string) string {
	cacheDir, err := os.UserCacheDir()
	if err != nil || cacheDir == "" {
		cacheDir = os.TempDir()
	}
	return filepath.Join(cacheDir, "oneall", "probe-agent", probeID+"-pending-results.json")
}

func nextBackoff(current time.Duration, maxDelay time.Duration) time.Duration {
	if current <= 0 {
		current = time.Second
	}
	next := current * 2
	if next > maxDelay {
		return maxDelay
	}
	return next
}

func newTraceID() string {
	var buf [8]byte
	if _, err := rand.Read(buf[:]); err == nil {
		return "trc_" + hex.EncodeToString(buf[:])
	}
	return fmt.Sprintf("trc_%d", time.Now().UnixNano())
}

func valueOrDefault(value string, fallback string) string {
	if value == "" {
		return fallback
	}
	return value
}
