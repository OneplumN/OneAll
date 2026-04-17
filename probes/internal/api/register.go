package api

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"github.com/one-pro/one-pro/probes/internal/config"
)

// RegistrationPayload is sent to the OneAll backend to register a new probe node.
type RegistrationPayload struct {
	Hostname          string            `json:"hostname"`
	IPAddress         string            `json:"ip_address,omitempty"`
	Location          string            `json:"location,omitempty"`
	NetworkType       string            `json:"network_type,omitempty"`
	SupportedProtocols []string          `json:"supported_protocols,omitempty"`
	AgentVersion      string            `json:"agent_version,omitempty"`
	Labels            map[string]string `json:"labels,omitempty"`
}

// RegistrationResponse contains credentials returned from the backend.
type RegistrationResponse struct {
	NodeID      string `json:"node_id"`
	APIToken    string `json:"api_token"`
	Name        string `json:"name"`
	Location    string `json:"location"`
	NetworkType string `json:"network_type"`
}

// RegisterProbe calls the backend registration endpoint using the provided config.
func RegisterProbe(ctx context.Context, cfg config.Config, payload RegistrationPayload) (RegistrationResponse, error) {
	var result RegistrationResponse
	base := cfg.APIBaseURL
	if base == "" {
		return result, fmt.Errorf("api_base_url is required for registration")
	}
	url := fmt.Sprintf("%s/api/probes/register/", base)

	body, err := json.Marshal(&payload)
	if err != nil {
		return result, fmt.Errorf("encode registration payload: %w", err)
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodPost, url, bytes.NewReader(body))
	if err != nil {
		return result, fmt.Errorf("build registration request: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")
	if cfg.BootstrapToken != "" {
		req.Header.Set("X-Probe-Bootstrap", cfg.BootstrapToken)
	}

	client := &http.Client{
		Timeout: cfg.RequestTimeout(),
	}
	resp, err := client.Do(req)
	if err != nil {
		return result, fmt.Errorf("registration request failed: %w", err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return result, fmt.Errorf("registration failed with status %d", resp.StatusCode)
	}
	ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
	defer cancel()
	decoder := json.NewDecoder(resp.Body)
	if err := decoder.Decode(&result); err != nil {
		return result, fmt.Errorf("decode registration response: %w", err)
	}
	if result.NodeID == "" || result.APIToken == "" {
		return result, fmt.Errorf("registration response missing node_id or api_token")
	}
	return result, nil
}

