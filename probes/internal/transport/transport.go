package transport

import (
	"context"

	"github.com/one-pro/one-pro/probes/internal/api"
	gateway "github.com/one-pro/one-pro/probes/internal/probes/v1"
)

// Transport encapsulates communication between probe and controller.
type Transport interface {
	SendHeartbeat(ctx context.Context, payload api.HeartbeatRequest) error
	FetchTasks(ctx context.Context, limit int) ([]api.Task, error)
	SubmitResult(ctx context.Context, result api.TaskResult) error
	PublishMetrics(ctx context.Context, payload api.MetricsPayload) error
	Close() error
	Commands() <-chan Command
}

// Command represents a control instruction from the controller.
type Command struct {
	Name         string
	Payload      map[string]any
	ConfigUpdate *gateway.ConfigUpdate
}
