package api

import (
	"context"
	"crypto/hmac"
	"crypto/sha256"
	"crypto/tls"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"net/http"
	"net/url"
	"path"
	"strconv"
	"strings"
	"time"
)

// Client is a thin wrapper around the OneAll backend API.
type Client struct {
	baseURL *url.URL
	nodeID  string
	token   string
	http    *http.Client
}

// NewClient constructs a Client with the provided timeout.
func NewClient(baseURL, nodeID, token string, timeout time.Duration, insecure bool) (*Client, error) {
	parsed, err := url.Parse(baseURL)
	if err != nil {
		return nil, fmt.Errorf("invalid api_base_url: %w", err)
	}
	transport := &http.Transport{}
	if parsed.Scheme == "https" && insecure {
		transport.TLSClientConfig = &tls.Config{InsecureSkipVerify: true} // #nosec G402
	}
	return &Client{
		baseURL: parsed,
		nodeID:  nodeID,
		token:   token,
		http: &http.Client{
			Timeout:   timeout,
			Transport: transport,
		},
	}, nil
}

func (c *Client) endpoint(parts ...string) string {
	clone := *c.baseURL
	segments := append([]string{clone.Path}, parts...)
	clone.Path = path.Join(segments...)
	return clone.String()
}

// FetchRemoteConfig retrieves remote configuration overrides for this node.
func (c *Client) FetchRemoteConfig(ctx context.Context) (RemoteConfigResponse, error) {
	var payload RemoteConfigResponse
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, c.endpoint("api", "probes", "nodes", c.nodeID, "config")+"/", nil)
	if err != nil {
		return payload, err
	}
	c.applyAuth(req)
	c.applySecurity(req, nil)
	resp, err := c.http.Do(req)
	if err != nil {
		return payload, err
	}
	defer resp.Body.Close()
	if resp.StatusCode == http.StatusNotFound {
		return payload, nil
	}
	if resp.StatusCode != http.StatusOK {
		return payload, fmt.Errorf("fetch config: unexpected status %d", resp.StatusCode)
	}
	if err := json.NewDecoder(resp.Body).Decode(&payload); err != nil {
		return payload, err
	}
	return payload, nil
}

func (c *Client) applyAuth(req *http.Request) {
	if c.token != "" {
		req.Header.Set("Authorization", "ProbeToken "+c.token)
	}
}

func (c *Client) applySecurity(req *http.Request, body []byte) {
	if c.token == "" {
		return
	}
	timestamp := strconv.FormatInt(time.Now().Unix(), 10)
	req.Header.Set("X-Probe-Timestamp", timestamp)
	signature := c.sign(timestamp, req.Method, req.URL.RequestURI(), body)
	req.Header.Set("X-Probe-Signature", signature)
}

func (c *Client) sign(timestamp, method, path string, body []byte) string {
	mac := hmac.New(sha256.New, []byte(c.token))
	mac.Write([]byte(timestamp))
	mac.Write([]byte("\n"))
	mac.Write([]byte(strings.ToUpper(method)))
	mac.Write([]byte("\n"))
	mac.Write([]byte(path))
	mac.Write([]byte("\n"))
	if len(body) > 0 {
		mac.Write(body)
	}
	return hex.EncodeToString(mac.Sum(nil))
}
