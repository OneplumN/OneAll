package agent

import (
	"context"
	"testing"
	"time"

	"github.com/rs/zerolog"

	"github.com/one-pro/one-pro/probes/internal/api"
	"github.com/one-pro/one-pro/probes/internal/config"
	"github.com/one-pro/one-pro/probes/internal/metrics"
	"github.com/one-pro/one-pro/probes/internal/plugins/registry"
	"github.com/one-pro/one-pro/probes/internal/storage"
	"github.com/one-pro/one-pro/probes/internal/transport"
)

type mockTransport struct {
	tasks          chan api.Task
	commands       chan transport.Command
	submitResultFn func(context.Context, api.TaskResult) error
}

func newMockTransport() *mockTransport {
	return &mockTransport{
		tasks:    make(chan api.Task),
		commands: make(chan transport.Command),
	}
}

func (m *mockTransport) SendHeartbeat(ctx context.Context, payload api.HeartbeatRequest) error {
	return nil
}

func (m *mockTransport) FetchTasks(ctx context.Context, limit int) ([]api.Task, error) {
	return nil, nil
}

func (m *mockTransport) Tasks() <-chan api.Task {
	return m.tasks
}

func (m *mockTransport) AcknowledgeTask(ctx context.Context, taskID string) error {
	return nil
}

func (m *mockTransport) SubmitResult(ctx context.Context, result api.TaskResult) error {
	if m.submitResultFn != nil {
		return m.submitResultFn(ctx, result)
	}
	return nil
}

func (m *mockTransport) PublishMetrics(ctx context.Context, payload api.MetricsPayload) error {
	return nil
}

func (m *mockTransport) Close() error {
	return nil
}

func (m *mockTransport) Commands() <-chan transport.Command {
	return m.commands
}

type blockingPlugin struct {
	started  chan struct{}
	release  chan struct{}
	executed chan api.TaskResult
}

func (p *blockingPlugin) Protocols() []string {
	return []string{"HTTPS"}
}

func (p *blockingPlugin) Execute(ctx context.Context, task api.Task) (api.TaskResult, error) {
	select {
	case <-p.started:
	default:
		close(p.started)
	}
	<-p.release
	if err := ctx.Err(); err != nil {
		return api.TaskResult{}, err
	}
	result := api.TaskResult{Status: "success", LatencyMs: 123}
	p.executed <- result
	return result, nil
}

type timeoutPlugin struct{}

func (p *timeoutPlugin) Protocols() []string {
	return []string{"HTTPS"}
}

func (p *timeoutPlugin) Execute(ctx context.Context, task api.Task) (api.TaskResult, error) {
	<-ctx.Done()
	return api.TaskResult{Status: "failed", Message: ctx.Err().Error()}, nil
}

func TestRunFlushesCachedResultsOnStart(t *testing.T) {
	t.Parallel()

	logger := zerolog.Nop()
	cache := storage.NewResultCache(t.TempDir()+"/results.json", 10, logger)
	cache.Enqueue(api.TaskResult{
		TaskID:    "cached-task",
		Protocol:  "HTTPS",
		Status:    "success",
		LatencyMs: 42,
	})

	submitted := make(chan api.TaskResult, 1)
	trans := newMockTransport()
	trans.submitResultFn = func(ctx context.Context, result api.TaskResult) error {
		submitted <- result
		return nil
	}

	ag := New(
		config.Config{MaxConcurrentTasks: 1},
		nil,
		registry.New(),
		logger,
		metrics.NewRecorder(),
		nil,
		cache,
		trans,
		nil,
	)

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	done := make(chan error, 1)
	go func() {
		done <- ag.Run(ctx)
	}()

	select {
	case result := <-submitted:
		if result.TaskID != "cached-task" {
			t.Fatalf("expected cached result to be flushed, got %q", result.TaskID)
		}
	case <-time.After(2 * time.Second):
		t.Fatal("timed out waiting for cached result flush")
	}

	cancel()

	select {
	case err := <-done:
		if err != context.Canceled {
			t.Fatalf("expected context cancellation, got %v", err)
		}
	case <-time.After(2 * time.Second):
		t.Fatal("timed out waiting for agent shutdown")
	}
}

func TestWorkerKeepsRunningTaskAliveAfterAgentContextCancelled(t *testing.T) {
	t.Parallel()

	logger := zerolog.Nop()
	reg := registry.New()
	plugin := &blockingPlugin{
		started:  make(chan struct{}),
		release:  make(chan struct{}),
		executed: make(chan api.TaskResult, 1),
	}
	reg.Register(plugin)

	submitted := make(chan api.TaskResult, 1)
	trans := newMockTransport()
	trans.submitResultFn = func(ctx context.Context, result api.TaskResult) error {
		submitted <- result
		return nil
	}

	ag := New(
		config.Config{MaxConcurrentTasks: 1, TaskRetryLimit: 1},
		nil,
		reg,
		logger,
		metrics.NewRecorder(),
		nil,
		nil,
		trans,
		nil,
	)

	agentCtx, cancelAgent := context.WithCancel(context.Background())
	defer cancelAgent()
	runCtx := context.Background()

	done := make(chan error, 1)
	go func() {
		done <- ag.workerLoop(agentCtx, runCtx, 1)
	}()

	ag.tasks <- api.Task{
		ID:             "task-1",
		Protocol:       "HTTPS",
		Target:         "https://code.heihuzi.ai/",
		TimeoutSeconds: 5,
	}

	select {
	case <-plugin.started:
	case <-time.After(2 * time.Second):
		t.Fatal("timed out waiting for task execution to start")
	}

	cancelAgent()
	close(plugin.release)

	select {
	case result := <-submitted:
		if result.Status != "success" {
			t.Fatalf("expected successful result submission, got %q", result.Status)
		}
	case <-time.After(2 * time.Second):
		t.Fatal("timed out waiting for task result submission")
	}

	select {
	case err := <-done:
		if err != context.Canceled {
			t.Fatalf("expected worker to stop on context cancellation, got %v", err)
		}
	case <-time.After(2 * time.Second):
		t.Fatal("timed out waiting for worker shutdown")
	}
}

func TestWorkerDrainsQueuedTasksBeforeStoppingOnAgentCancellation(t *testing.T) {
	t.Parallel()

	logger := zerolog.Nop()
	reg := registry.New()
	plugin := &blockingPlugin{
		started:  make(chan struct{}),
		release:  make(chan struct{}),
		executed: make(chan api.TaskResult, 2),
	}
	reg.Register(plugin)

	submitted := make(chan api.TaskResult, 2)
	trans := newMockTransport()
	trans.submitResultFn = func(ctx context.Context, result api.TaskResult) error {
		submitted <- result
		return nil
	}

	ag := New(
		config.Config{MaxConcurrentTasks: 1, TaskRetryLimit: 1},
		nil,
		reg,
		logger,
		metrics.NewRecorder(),
		nil,
		nil,
		trans,
		nil,
	)

	agentCtx, cancelAgent := context.WithCancel(context.Background())
	defer cancelAgent()
	runCtx := context.Background()

	done := make(chan error, 1)
	go func() {
		done <- ag.workerLoop(agentCtx, runCtx, 1)
	}()

	ag.tasks <- api.Task{
		ID:             "task-1",
		Protocol:       "HTTPS",
		Target:         "https://code.heihuzi.ai/",
		TimeoutSeconds: 5,
	}
	ag.tasks <- api.Task{
		ID:             "task-2",
		Protocol:       "HTTPS",
		Target:         "https://code.heihuzi.ai/",
		TimeoutSeconds: 5,
	}

	select {
	case <-plugin.started:
	case <-time.After(2 * time.Second):
		t.Fatal("timed out waiting for first task execution to start")
	}

	cancelAgent()
	close(plugin.release)

	for i := 0; i < 2; i++ {
		select {
		case <-submitted:
		case <-time.After(2 * time.Second):
			t.Fatalf("timed out waiting for submitted result %d", i+1)
		}
	}

	select {
	case err := <-done:
		if err != context.Canceled {
			t.Fatalf("expected worker to stop on context cancellation, got %v", err)
		}
	case <-time.After(2 * time.Second):
		t.Fatal("timed out waiting for worker shutdown")
	}
}

func TestHandleTaskReportsExecutionDeadlineAsTimeout(t *testing.T) {
	t.Parallel()

	logger := zerolog.Nop()
	reg := registry.New()
	reg.Register(&timeoutPlugin{})

	submitted := make(chan api.TaskResult, 1)
	trans := newMockTransport()
	trans.submitResultFn = func(ctx context.Context, result api.TaskResult) error {
		submitted <- result
		return nil
	}

	ag := New(
		config.Config{MaxConcurrentTasks: 1, TaskRetryLimit: 1},
		nil,
		reg,
		logger,
		metrics.NewRecorder(),
		nil,
		nil,
		trans,
		nil,
	)

	ag.handleTask(context.Background(), api.Task{
		ID:             "task-timeout",
		Protocol:       "HTTPS",
		Target:         "https://example.com/",
		TimeoutSeconds: 1,
	})

	select {
	case result := <-submitted:
		if result.Status != "timeout" {
			t.Fatalf("expected timeout status, got %q", result.Status)
		}
		if result.Message == "" {
			t.Fatal("expected timeout message to be preserved")
		}
	case <-time.After(3 * time.Second):
		t.Fatal("timed out waiting for timeout result submission")
	}
}

var _ transport.Transport = (*mockTransport)(nil)
var _ registry.Plugin = (*blockingPlugin)(nil)
var _ registry.Plugin = (*timeoutPlugin)(nil)
