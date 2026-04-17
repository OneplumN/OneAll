package config

import (
	"os"
	"path/filepath"
	"testing"
)

func TestLoadAppliesProbeEnvOverrides(t *testing.T) {
	t.Setenv("PROBE_API_BASE_URL", "http://backend:8000")
	t.Setenv("PROBE_GRPC_GATEWAY", "grpc-gateway:50051")
	t.Setenv("PROBE_GRPC_INSECURE", "true")
	t.Setenv("PROBE_BOOTSTRAP_TOKEN", "bootstrap-from-env")
	t.Setenv("PROBE_HEARTBEAT_INTERVAL", "45")
	t.Setenv("PROBE_RESULT_CACHE_PATH", "/var/lib/oneall-probe/cache/results.json")

	configPath := filepath.Join(t.TempDir(), "config.yaml")
	configBody := []byte(`
api_base_url: "http://127.0.0.1:8000"
grpc_gateway: "127.0.0.1:50051"
grpc_insecure: false
bootstrap_token: ""
heartbeat_interval: 30
result_cache_path: "/tmp/results.json"
`)
	if err := os.WriteFile(configPath, configBody, 0o600); err != nil {
		t.Fatalf("write config: %v", err)
	}

	cfg, err := Load(configPath)
	if err != nil {
		t.Fatalf("load config: %v", err)
	}

	if cfg.APIBaseURL != "http://backend:8000" {
		t.Fatalf("unexpected api base url: %s", cfg.APIBaseURL)
	}
	if cfg.GRPCGateway != "grpc-gateway:50051" {
		t.Fatalf("unexpected grpc gateway: %s", cfg.GRPCGateway)
	}
	if !cfg.GRPCInsecure {
		t.Fatalf("expected grpc_insecure to be overridden")
	}
	if cfg.BootstrapToken != "bootstrap-from-env" {
		t.Fatalf("unexpected bootstrap token: %s", cfg.BootstrapToken)
	}
	if cfg.HeartbeatIntervalSec != 45 {
		t.Fatalf("unexpected heartbeat interval: %d", cfg.HeartbeatIntervalSec)
	}
	if cfg.ResultCachePath != "/var/lib/oneall-probe/cache/results.json" {
		t.Fatalf("unexpected cache path: %s", cfg.ResultCachePath)
	}
}
