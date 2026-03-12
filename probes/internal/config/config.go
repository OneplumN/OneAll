package config

import (
	"fmt"
	"os"
	"time"

	"gopkg.in/yaml.v3"
)

// Config describes the runtime settings for a probe node.
type Config struct {
	APIBaseURL           string `yaml:"api_base_url"`
	NodeID               string `yaml:"node_id"`
	APIToken             string `yaml:"api_token"`
	GRPCGateway          string `yaml:"grpc_gateway"`
	GRPCInsecure         bool   `yaml:"grpc_insecure"`
	GRPCCAFile           string `yaml:"grpc_ca_file"`
	GRPCClientCert       string `yaml:"grpc_client_cert"`
	GRPCClientKey        string `yaml:"grpc_client_key"`
	HeartbeatIntervalSec int    `yaml:"heartbeat_interval"`
	TaskPollIntervalSec  int    `yaml:"task_poll_interval"`
	RequestTimeoutSec    int    `yaml:"request_timeout"`
	InsecureSkipTLS      bool   `yaml:"insecure_skip_tls"`
	MaxConcurrentTasks   int    `yaml:"max_concurrent_tasks"`
	TaskRetryLimit       int    `yaml:"task_retry_limit"`
	MetricsAddr          string `yaml:"metrics_addr"`
	ResultCachePath      string `yaml:"result_cache_path"`
	ResultCacheLimit     int    `yaml:"result_cache_limit"`
	UpdateDir            string `yaml:"update_dir"`
	ScheduleStorePath    string `yaml:"schedule_store_path"`
}

// HeartbeatInterval exposes the configured heartbeat ticker duration.
func (c Config) HeartbeatInterval() time.Duration {
	if c.HeartbeatIntervalSec <= 0 {
		return 30 * time.Second
	}
	return time.Duration(c.HeartbeatIntervalSec) * time.Second
}

// TaskPollInterval exposes the configured task polling duration.
func (c Config) TaskPollInterval() time.Duration {
	if c.TaskPollIntervalSec <= 0 {
		return 15 * time.Second
	}
	return time.Duration(c.TaskPollIntervalSec) * time.Second
}

// RequestTimeout returns the HTTP request timeout.
func (c Config) RequestTimeout() time.Duration {
	if c.RequestTimeoutSec <= 0 {
		return 10 * time.Second
	}
	return time.Duration(c.RequestTimeoutSec) * time.Second
}

// MaxConcurrency returns the allowed number of concurrent task executions.
func (c Config) MaxConcurrency() int {
	if c.MaxConcurrentTasks <= 0 {
		return 4
	}
	return c.MaxConcurrentTasks
}

// RetryLimit returns how many times a task can be retried locally.
func (c Config) RetryLimit() int {
	if c.TaskRetryLimit <= 0 {
		return 1
	}
	return c.TaskRetryLimit
}

// Load reads the YAML configuration from disk.
func Load(path string) (Config, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return Config{}, fmt.Errorf("read config: %w", err)
	}
	var cfg Config
	if err := yaml.Unmarshal(data, &cfg); err != nil {
		return Config{}, fmt.Errorf("parse config: %w", err)
	}
	if cfg.APIBaseURL == "" {
		return Config{}, fmt.Errorf("api_base_url is required")
	}
	if cfg.NodeID == "" {
		return Config{}, fmt.Errorf("node_id is required")
	}
	if cfg.APIToken == "" {
		return Config{}, fmt.Errorf("api_token is required")
	}
	return cfg, nil
}

// UseGRPC reports whether the probe should attempt to connect via gRPC gateway.
func (c Config) UseGRPC() bool {
	return c.GRPCGateway != ""
}
