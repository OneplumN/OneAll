package config

import (
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"time"

	"gopkg.in/yaml.v3"
)

// Config describes the runtime settings for a probe node.
type Config struct {
	APIBaseURL           string `yaml:"api_base_url"`
	NodeID               string `yaml:"node_id"`
	APIToken             string `yaml:"api_token"`
	BootstrapToken       string `yaml:"bootstrap_token"`
	Location             string `yaml:"location"`
	NetworkType          string `yaml:"network_type"`
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
	if err := applyEnvOverrides(&cfg); err != nil {
		return Config{}, err
	}
	if cfg.APIBaseURL == "" {
		return Config{}, fmt.Errorf("api_base_url is required")
	}
	// 在开发和大多数生产场景下，node_id / api_token / bootstrap_token 都可以留空，
	// 由探针在启动时通过自动注册获取凭据。是否需要引导 token 由服务端配置控制。
	return cfg, nil
}

func applyEnvOverrides(cfg *Config) error {
	if cfg == nil {
		return nil
	}

	applyString := func(name string, target *string) {
		if value, ok := os.LookupEnv(name); ok && value != "" {
			*target = value
		}
	}
	applyBool := func(name string, target *bool) error {
		value, ok := os.LookupEnv(name)
		if !ok || value == "" {
			return nil
		}
		parsed, err := strconv.ParseBool(value)
		if err != nil {
			return fmt.Errorf("invalid %s: %w", name, err)
		}
		*target = parsed
		return nil
	}
	applyInt := func(name string, target *int) error {
		value, ok := os.LookupEnv(name)
		if !ok || value == "" {
			return nil
		}
		parsed, err := strconv.Atoi(value)
		if err != nil {
			return fmt.Errorf("invalid %s: %w", name, err)
		}
		*target = parsed
		return nil
	}

	applyString("PROBE_API_BASE_URL", &cfg.APIBaseURL)
	applyString("PROBE_NODE_ID", &cfg.NodeID)
	applyString("PROBE_API_TOKEN", &cfg.APIToken)
	applyString("PROBE_BOOTSTRAP_TOKEN", &cfg.BootstrapToken)
	applyString("PROBE_LOCATION", &cfg.Location)
	applyString("PROBE_NETWORK_TYPE", &cfg.NetworkType)
	applyString("PROBE_GRPC_GATEWAY", &cfg.GRPCGateway)
	applyString("PROBE_GRPC_CA_FILE", &cfg.GRPCCAFile)
	applyString("PROBE_GRPC_CLIENT_CERT", &cfg.GRPCClientCert)
	applyString("PROBE_GRPC_CLIENT_KEY", &cfg.GRPCClientKey)
	applyString("PROBE_METRICS_ADDR", &cfg.MetricsAddr)
	applyString("PROBE_RESULT_CACHE_PATH", &cfg.ResultCachePath)
	applyString("PROBE_UPDATE_DIR", &cfg.UpdateDir)
	applyString("PROBE_SCHEDULE_STORE_PATH", &cfg.ScheduleStorePath)

	if err := applyBool("PROBE_GRPC_INSECURE", &cfg.GRPCInsecure); err != nil {
		return err
	}
	if err := applyBool("PROBE_INSECURE_SKIP_TLS", &cfg.InsecureSkipTLS); err != nil {
		return err
	}
	if err := applyInt("PROBE_HEARTBEAT_INTERVAL", &cfg.HeartbeatIntervalSec); err != nil {
		return err
	}
	if err := applyInt("PROBE_TASK_POLL_INTERVAL", &cfg.TaskPollIntervalSec); err != nil {
		return err
	}
	if err := applyInt("PROBE_REQUEST_TIMEOUT", &cfg.RequestTimeoutSec); err != nil {
		return err
	}
	if err := applyInt("PROBE_MAX_CONCURRENT_TASKS", &cfg.MaxConcurrentTasks); err != nil {
		return err
	}
	if err := applyInt("PROBE_TASK_RETRY_LIMIT", &cfg.TaskRetryLimit); err != nil {
		return err
	}
	if err := applyInt("PROBE_RESULT_CACHE_LIMIT", &cfg.ResultCacheLimit); err != nil {
		return err
	}

	return nil
}

// UseGRPC reports whether the probe should attempt to connect via gRPC gateway.
func (c Config) UseGRPC() bool {
	return c.GRPCGateway != ""
}

// StatePath derives a reasonable default path for storing dynamic probe state.
func StatePath(cfg Config, configPath string) string {
	// Prefer colocating with result cache if configured.
	if cfg.ResultCachePath != "" {
		dir := filepath.Dir(cfg.ResultCachePath)
		return filepath.Join(dir, "probe-state.yaml")
	}
	// Fall back to a per-user config directory.
	if dir, err := os.UserConfigDir(); err == nil && dir != "" {
		return filepath.Join(dir, "oneall", "probe-state.yaml")
	}
	// Last resort: alongside the provided config file or current directory.
	if configPath != "" {
		if abs, err := filepath.Abs(configPath); err == nil {
			return filepath.Join(filepath.Dir(abs), "probe-state.yaml")
		}
	}
	return "probe-state.yaml"
}

type state struct {
	NodeID        string    `yaml:"node_id"`
	APIToken      string    `yaml:"api_token"`
	RegisteredAt  time.Time `yaml:"registered_at,omitempty"`
	LastHeartbeat time.Time `yaml:"last_heartbeat_at,omitempty"`
}

// LoadState applies persisted node credentials from the given path into cfg.
// Missing state file is not considered an error.
func LoadState(path string, cfg *Config) error {
	if path == "" || cfg == nil {
		return nil
	}
	data, err := os.ReadFile(path)
	if err != nil {
		if os.IsNotExist(err) {
			return nil
		}
		return fmt.Errorf("read state: %w", err)
	}
	var st state
	if err := yaml.Unmarshal(data, &st); err != nil {
		return fmt.Errorf("parse state: %w", err)
	}
	if cfg.NodeID == "" && st.NodeID != "" {
		cfg.NodeID = st.NodeID
	}
	if cfg.APIToken == "" && st.APIToken != "" {
		cfg.APIToken = st.APIToken
	}
	return nil
}

// PersistState writes the node credentials from cfg to the given path.
func PersistState(path string, cfg Config) error {
	if path == "" {
		return nil
	}
	if cfg.NodeID == "" || cfg.APIToken == "" {
		// Nothing to persist.
		return nil
	}
	st := state{
		NodeID:       cfg.NodeID,
		APIToken:     cfg.APIToken,
		RegisteredAt: time.Now().UTC(),
	}
	data, err := yaml.Marshal(&st)
	if err != nil {
		return fmt.Errorf("marshal state: %w", err)
	}
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return fmt.Errorf("ensure state dir: %w", err)
	}
	if err := os.WriteFile(path, data, 0o600); err != nil {
		return fmt.Errorf("write state: %w", err)
	}
	return nil
}
