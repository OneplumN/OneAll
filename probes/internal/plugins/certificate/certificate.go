package certificate

import (
	"context"
	"crypto/tls"
	"encoding/json"
	"errors"
	"fmt"
	"math"
	"net"
	"net/url"
	"strconv"
	"strings"
	"time"

	"github.com/one-pro/one-pro/probes/internal/api"
	"github.com/one-pro/one-pro/probes/internal/plugins/registry"
)

const (
	defaultPort             = "443"
	defaultWarningDays      = 7
	certificateStatusOK     = "valid"
	certificateStatusSoon   = "expires_soon"
	certificateStatusExpired = "expired"
	certificateStatusError  = "error"
)

// Probe validates TLS certificate metadata for HTTPS-like targets.
type Probe struct {
	timeout     time.Duration
	warningDays int
}

// New creates a certificate probe with dial timeout and warning threshold.
func New(timeout time.Duration, warningDays int) *Probe {
	if warningDays <= 0 {
		warningDays = defaultWarningDays
	}
	return &Probe{timeout: timeout, warningDays: warningDays}
}

// Register wires the certificate probe into the registry.
func Register(reg *registry.Registry, timeout time.Duration) {
	reg.Register(New(timeout, defaultWarningDays))
}

// Protocols advertises supported protocol identifiers.
func (p *Probe) Protocols() []string {
	return []string{"CERTIFICATE"}
}

type certificateInfo struct {
	notBefore time.Time
	notAfter  time.Time
	issuer    string
	subject   string
}

// Execute inspects the remote certificate and returns a health report.
func (p *Probe) Execute(ctx context.Context, task api.Task) (api.TaskResult, error) {
	if task.Target == "" {
		return api.TaskResult{Status: "failed", Message: "missing target"}, nil
	}
	host, port, err := parseTarget(task.Target)
	if err != nil {
		return api.TaskResult{Status: "failed", Message: err.Error()}, nil
	}
	warning := warningDaysFromMetadata(task.Metadata, p.warningDays)
	started := time.Now()
	info, err := p.inspectCertificate(ctx, host, port)
	if err != nil {
		return api.TaskResult{
			Status:    "failed",
			Message:   err.Error(),
			LatencyMs: int(time.Since(started).Milliseconds()),
			Metadata: map[string]any{
				"certificate": map[string]any{
					"status":                 certificateStatusError,
					"issuer":                 "",
					"subject":                "",
					"message":                err.Error(),
					"warning_threshold_days": warning,
				},
			},
		}, nil
	}
	days := daysUntilExpiry(info.notAfter)
	status, humanMessage, success := evaluateCertificate(days, warning)
	meta := map[string]any{
		"certificate": map[string]any{
			"status":                 status,
			"days_until_expiry":      days,
			"issuer":                 info.issuer,
			"subject":                info.subject,
			"valid_from":             info.notBefore.UTC().Format(time.RFC3339),
			"valid_to":               info.notAfter.UTC().Format(time.RFC3339),
			"warning_threshold_days": warning,
		},
	}
	result := api.TaskResult{
		Status:    "success",
		Message:   humanMessage,
		LatencyMs: int(time.Since(started).Milliseconds()),
		Metadata:  meta,
	}
	if !success {
		result.Status = "failed"
		if result.Message == "" {
			result.Message = "证书已过期"
		}
	}
	return result, nil
}

func (p *Probe) inspectCertificate(ctx context.Context, host, port string) (*certificateInfo, error) {
	dialer := &net.Dialer{Timeout: p.timeout}
	conn, err := dialer.DialContext(ctx, "tcp", net.JoinHostPort(host, port))
	if err != nil {
		return nil, err
	}
	deadline := time.Now().Add(p.timeout)
	_ = conn.SetDeadline(deadline)
	client := tls.Client(conn, &tls.Config{ServerName: host})
	defer client.Close()
	if err := client.HandshakeContext(ctx); err != nil {
		return nil, err
	}
	state := client.ConnectionState()
	if len(state.PeerCertificates) == 0 {
		return nil, errors.New("peer certificate missing")
	}
	cert := state.PeerCertificates[0]
	return &certificateInfo{
		notBefore: cert.NotBefore,
		notAfter:  cert.NotAfter,
		issuer:    cert.Issuer.CommonName,
		subject:   cert.Subject.CommonName,
	}, nil
}

func parseTarget(raw string) (string, string, error) {
	if raw == "" {
		return "", "", errors.New("invalid target")
	}
	value := raw
	if !strings.Contains(value, "://") {
		value = "https://" + value
	}
	parsed, err := url.Parse(value)
	if err != nil {
		return "", "", fmt.Errorf("invalid target: %w", err)
	}
	host := parsed.Hostname()
	if host == "" {
		return "", "", errors.New("invalid host")
	}
	port := parsed.Port()
	if port == "" {
		port = defaultPort
	}
	return host, port, nil
}

func warningDaysFromMetadata(meta map[string]any, fallback int) int {
	if fallback <= 0 {
		fallback = defaultWarningDays
	}
	if meta == nil {
		return fallback
	}
	if val := parseInt(meta["warning_threshold_days"]); val > 0 {
		return val
	}
	if cfg, ok := meta["config"].(map[string]any); ok {
		if val := parseInt(cfg["warning_threshold_days"]); val > 0 {
			return val
		}
	}
	return fallback
}

func parseInt(value any) int {
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
	case json.Number:
		if val, err := v.Int64(); err == nil {
			return int(val)
		}
	case string:
		num, err := strconv.Atoi(strings.TrimSpace(v))
		if err == nil {
			return num
		}
	}
	return 0
}

func daysUntilExpiry(notAfter time.Time) int {
	seconds := notAfter.UTC().Sub(time.Now().UTC()).Seconds()
	return int(math.Round(seconds / 86400.0))
}

func evaluateCertificate(days int, warning int) (string, string, bool) {
	switch {
	case days < 0:
		return certificateStatusExpired, "证书已过期", false
	case days <= warning:
		return certificateStatusSoon, "证书即将过期", true
	default:
		return certificateStatusOK, "", true
	}
}
