package api

import "time"

// Task represents a detection job fetched from the controller.
type Task struct {
	ID             string         `json:"id"`
	ScheduleID     string         `json:"schedule_id,omitempty"`
	Protocol       string         `json:"protocol"`
	Target         string         `json:"target"`
	TimeoutSeconds int            `json:"timeout_seconds"`
	ExpectStatus   int            `json:"expect_status"`
	Metadata       map[string]any `json:"metadata"`
	ScheduledAt    time.Time      `json:"scheduled_at"`
	Missed         bool           `json:"missed,omitempty"`
}

// TaskResult captures the probe execution outcome.
type TaskResult struct {
	TaskID      string         `json:"task_id"`
	ScheduleID  string         `json:"schedule_id,omitempty"`
	Protocol    string         `json:"protocol"`
	Status      string         `json:"status"`
	Message     string         `json:"message,omitempty"`
	LatencyMs   int            `json:"latency_ms"`
	StatusCode  int            `json:"status_code,omitempty"`
	Metadata    map[string]any `json:"metadata,omitempty"`
	ScheduledAt time.Time      `json:"scheduled_at"`
	FinishedAt  time.Time      `json:"finished_at"`
}

// HeartbeatRequest is sent periodically so the controller knows probes are alive.
type HeartbeatRequest struct {
	NodeID             string             `json:"node_id"`
	SentAt             time.Time          `json:"sent_at"`
	Status             string             `json:"status"`
	SupportedProtocols []string           `json:"supported_protocols,omitempty"`
	Metrics            map[string]float64 `json:"metrics,omitempty"`
	IPAddress          string             `json:"ip_address,omitempty"`
}

// MetricsPayload represents a probe runtime snapshot pushed to the controller.
type MetricsPayload struct {
	CapturedAt    time.Time           `json:"captured_at"`
	UptimeSeconds int64               `json:"uptime_seconds"`
	Heartbeats    MetricsHeartbeat    `json:"heartbeats"`
	CPUUsage      float64             `json:"cpu_usage"`
	MemoryUsageMB float64             `json:"memory_usage_mb"`
	Tasks         MetricsTaskCounters `json:"tasks"`
	Queue         MetricsQueueGauge   `json:"queue"`
	Workers       MetricsWorkerGauge  `json:"workers"`
}

// MetricsHeartbeat holds counters for heartbeats.
type MetricsHeartbeat struct {
	Sent        int64      `json:"sent"`
	Failed      int64      `json:"failed"`
	LastSuccess *time.Time `json:"last_success,omitempty"`
}

// MetricsTaskCounters captures task throughput.
type MetricsTaskCounters struct {
	Fetched  int64 `json:"fetched"`
	Executed int64 `json:"executed"`
	Failed   int64 `json:"failed"`
}

// MetricsQueueGauge exposes queue depth information.
type MetricsQueueGauge struct {
	Depth    int64 `json:"depth"`
	Capacity int64 `json:"capacity"`
}

// MetricsWorkerGauge captures worker utilization.
type MetricsWorkerGauge struct {
	Active int64 `json:"active"`
}

// RemoteConfigResponse describes dynamic configuration overrides from backend.
type RemoteConfigResponse struct {
	Version            string             `json:"version"`
	HeartbeatInterval  int                `json:"heartbeat_interval"`
	TaskPollInterval   int                `json:"task_poll_interval"`
	MaxConcurrentTasks int                `json:"max_concurrent_tasks"`
	EnabledProtocols   []string           `json:"enabled_protocols"`
	LogLevel           string             `json:"log_level"`
	Update             *UpdateInstruction `json:"update,omitempty"`
}

// UpdateInstruction describes a remote self-update payload.
type UpdateInstruction struct {
	Version     string `json:"version"`
	DownloadURL string `json:"download_url"`
	SHA256      string `json:"sha256"`
}
