package agent

import (
	"context"
	"errors"
	"fmt"
	"os"
	"strings"
	"time"

	"github.com/rs/zerolog"
	"golang.org/x/sync/errgroup"

	"github.com/one-pro/one-pro/probes/internal/api"
	"github.com/one-pro/one-pro/probes/internal/config"
	"github.com/one-pro/one-pro/probes/internal/control"
	"github.com/one-pro/one-pro/probes/internal/metrics"
	"github.com/one-pro/one-pro/probes/internal/plugins/registry"
	"github.com/one-pro/one-pro/probes/internal/scheduler"
	"github.com/one-pro/one-pro/probes/internal/storage"
	"github.com/one-pro/one-pro/probes/internal/system"
	"github.com/one-pro/one-pro/probes/internal/transport"
)

// Agent coordinates heartbeat, task polling and plugin execution.
type Agent struct {
	cfg       config.Config
	client    *api.Client
	registry  *registry.Registry
	logger    zerolog.Logger
	tasks     chan api.Task
	metrics   *metrics.Recorder
	settings  control.Settings
	cache     *storage.ResultCache
	transport transport.Transport
	scheduler *scheduler.Manager
}

const metricsPushInterval = 30 * time.Second
const directClaimPollInterval = time.Second

// New creates a configured Agent instance.
func New(
	cfg config.Config,
	client *api.Client,
	reg *registry.Registry,
	logger zerolog.Logger,
	recorder *metrics.Recorder,
	settings control.Settings,
	cache *storage.ResultCache,
	t transport.Transport,
	storage scheduler.Storage,
) *Agent {
	if t == nil {
		panic("transport cannot be nil")
	}
	queueSize := cfg.MaxConcurrency()
	if queueSize < 1 {
		queueSize = 1
	}
	agent := &Agent{
		cfg:       cfg,
		client:    client,
		registry:  reg,
		logger:    logger,
		tasks:     make(chan api.Task, queueSize*2),
		metrics:   recorder,
		settings:  settings,
		cache:     cache,
		transport: t,
	}
	agent.scheduler = scheduler.NewManager(logger, agent.tasks, storage)
	if recorder != nil {
		recorder.SetQueue(0, cap(agent.tasks))
	}
	return agent
}

// Run starts the agent loops until the context is cancelled.
func (a *Agent) Run(ctx context.Context) error {
	runCtx := ctx
	eg, agentCtx := errgroup.WithContext(ctx)
	a.flushCachedResults()
	eg.Go(func() error { return a.heartbeatLoop(agentCtx) })
	eg.Go(func() error { return a.taskLoop(agentCtx) })
	eg.Go(func() error { return a.claimLoop(agentCtx) })
	a.startCommandLoop(agentCtx)
	a.startMetricsReporter(agentCtx)
	if a.scheduler != nil {
		a.scheduler.Start(agentCtx)
	}
	workerCount := a.cfg.MaxConcurrency()
	if a.settings != nil {
		workerCount = a.settings.MaxConcurrency()
	}
	if workerCount < 1 {
		workerCount = 1
	}
	for i := 0; i < workerCount; i++ {
		workerID := i + 1
		eg.Go(func() error { return a.workerLoop(agentCtx, runCtx, workerID) })
	}
	return eg.Wait()
}

func (a *Agent) claimLoop(ctx context.Context) error {
	if a.client == nil {
		<-ctx.Done()
		return ctx.Err()
	}

	for {
		select {
		case <-ctx.Done():
			return ctx.Err()
		default:
		}

		if len(a.tasks) >= cap(a.tasks) {
			if err := a.wait(ctx, a.claimInterval()); err != nil {
				return err
			}
			continue
		}

		task, err := a.client.ClaimOneOffTask(ctx, 1)
		if err != nil {
			if ctx.Err() != nil || errors.Is(err, context.Canceled) {
				return ctx.Err()
			}
			a.logger.Warn().Err(err).Msg("failed to claim one-off task")
			if err := a.wait(ctx, a.claimInterval()); err != nil {
				return err
			}
			continue
		}
		if task == nil {
			if err := a.wait(ctx, a.claimInterval()); err != nil {
				return err
			}
			continue
		}

		select {
		case <-ctx.Done():
			return ctx.Err()
		case a.tasks <- *task:
			if a.metrics != nil {
				a.metrics.IncTasksFetched(1)
			}
			a.logger.Debug().
				Str("task_id", task.ID).
				Str("protocol", task.Protocol).
				Str("target", task.Target).
				Msg("claimed one-off task")
			a.recordQueueDepth()
		}
	}
}

func (a *Agent) taskLoop(ctx context.Context) error {
	a.logger.Info().Msg("task loop started")
	tasksCh := a.transport.Tasks()
	if tasksCh == nil {
		return errors.New("transport task channel is not available")
	}
	for {
		select {
		case <-ctx.Done():
			return ctx.Err()
		case task, ok := <-tasksCh:
			if !ok {
				return errors.New("transport task channel closed")
			}
			select {
			case <-ctx.Done():
				return ctx.Err()
			case a.tasks <- task:
				if a.metrics != nil {
					a.metrics.IncTasksFetched(1)
				}
				if err := a.transport.AcknowledgeTask(ctx, task.ID); err != nil {
					a.logger.Warn().Err(err).Str("task_id", task.ID).Msg("failed to acknowledge task receipt")
				}
				a.logger.Debug().
					Str("task_id", task.ID).
					Str("schedule_id", task.ScheduleID).
					Str("protocol", task.Protocol).
					Str("target", task.Target).
					Msg("queued task from transport")
				a.recordQueueDepth()
			}
		}
	}
}

func (a *Agent) heartbeatLoop(ctx context.Context) error {
	a.logger.Info().Msg("heartbeat loop started")
	// 当连续心跳失败达到一定次数时，将错误返回给上层，由上层负责重建连接 / 重启 agent。
	const maxFailureStreak = 5
	failureStreak := 0

	for {
		snapshot := a.metrics.Snapshot()
		hostStats := system.Collect()
		if a.metrics != nil {
			a.metrics.SetHostUsage(hostStats.CPUPercent, hostStats.MemoryMB)
		}
		metrics := map[string]float64{
			"cpu_usage":        hostStats.CPUPercent,
			"memory_usage_mb":  hostStats.MemoryMB,
			"memory_usage_pct": hostStats.MemoryPercent,
			"load_avg":         hostStats.Load1,
			"queue_depth":      float64(snapshot.Queue.Depth),
			"active_tasks":     float64(snapshot.Workers.Active),
		}
		payload := api.HeartbeatRequest{
			SentAt:             time.Now().UTC(),
			Status:             "online",
			SupportedProtocols: a.registeredProtocols(),
			Metrics:            metrics,
			IPAddress:          hostStats.IP,
		}
		if err := a.transport.SendHeartbeat(ctx, payload); err != nil {
			a.logger.Warn().Err(err).Msg("failed to send heartbeat")
			a.recordHeartbeat(false)
			failureStreak++
			// 无论错误类型，只要连续失败达到一定次数，就返回错误，
			// 交由上层重建 gRPC 连接，避免长时间停留在“连接已坏”的状态。
			if failureStreak >= maxFailureStreak {
				a.logger.Error().
					Err(err).
					Int("failure_streak", failureStreak).
					Msg("heartbeat failed repeatedly; giving up and requesting reconnect")
				return err
			}
		} else {
			a.logger.Debug().Msg("heartbeat acknowledged")
			a.recordHeartbeat(true)
			if failureStreak > 0 {
				a.logger.Info().Int("failure_streak", failureStreak).Msg("heartbeat recovered")
			}
			failureStreak = 0
		}
		if err := a.wait(ctx, a.currentHeartbeatInterval()); err != nil {
			return err
		}
	}
}

func (a *Agent) workerLoop(ctx context.Context, runCtx context.Context, id int) error {
	a.logger.Info().Int("worker", id).Msg("worker started")
	for {
		task, ok := a.nextTask(ctx)
		if !ok {
			return ctx.Err()
		}
		a.recordQueueDepth()
		a.setWorkerDelta(1)
		a.handleTask(runCtx, task)
		a.setWorkerDelta(-1)
	}
}

func (a *Agent) nextTask(ctx context.Context) (api.Task, bool) {
	select {
	case task := <-a.tasks:
		return task, true
	default:
	}

	select {
	case task := <-a.tasks:
		return task, true
	case <-ctx.Done():
		return api.Task{}, false
	}
}

func (a *Agent) handleTask(ctx context.Context, task api.Task) {
	if task.Missed {
		a.logger.Warn().
			Str("schedule", task.ScheduleID).
			Time("scheduled_at", task.ScheduledAt).
			Msg("schedule missed; reporting failure")
		result := api.TaskResult{
			TaskID:      task.ID,
			ScheduleID:  task.ScheduleID,
			Protocol:    task.Protocol,
			Status:      "missed",
			Message:     fmt.Sprintf("execution missed; scheduled at %s", task.ScheduledAt.Format(time.RFC3339)),
			ScheduledAt: task.ScheduledAt,
		}
		a.submitResult(ctx, result)
		a.recordTaskExecution(result.Status)
		return
	}
	plugin, err := a.registry.Get(task.Protocol)
	if err != nil {
		a.logger.Warn().Err(err).Str("protocol", task.Protocol).Msg("missing plugin")
		return
	}
	a.logger.Info().
		Str("task_id", task.ID).
		Str("schedule_id", task.ScheduleID).
		Str("protocol", task.Protocol).
		Str("target", task.Target).
		Time("scheduled_at", task.ScheduledAt).
		Msg("worker starting task")
	maxAttempts := a.cfg.RetryLimit()
	if maxAttempts < 1 {
		maxAttempts = 1
	}
	var lastResult api.TaskResult
	for attempt := 1; attempt <= maxAttempts; attempt++ {
		execCtx, cancel := context.WithTimeout(context.WithoutCancel(ctx), time.Duration(task.TimeoutSeconds)*time.Second)
		result, err := plugin.Execute(execCtx, task)
		if err != nil {
			result = api.TaskResult{
				Status:  "failed",
				Message: err.Error(),
			}
		}
		result = normalizeTaskResult(result, execCtx.Err())
		cancel()
		result.TaskID = task.ID
		result.ScheduleID = task.ScheduleID
		result.Protocol = task.Protocol
		result.ScheduledAt = task.ScheduledAt
		result.FinishedAt = time.Now().UTC()
		if result.Status == "" {
			result.Status = "success"
		}
		lastResult = result
		if result.Status == "success" {
			break
		}
		if attempt < maxAttempts {
			a.logger.Warn().Str("task_id", task.ID).Int("attempt", attempt).Msg("task failed, retrying")
		}
	}
	a.submitResult(ctx, lastResult)
	a.logger.Info().
		Str("task_id", lastResult.TaskID).
		Str("schedule_id", lastResult.ScheduleID).
		Str("status", lastResult.Status).
		Int("status_code", lastResult.StatusCode).
		Int("latency_ms", lastResult.LatencyMs).
		Time("scheduled_at", lastResult.ScheduledAt).
		Msg("worker finished task")
	a.recordTaskExecution(lastResult.Status)
}

func normalizeTaskResult(result api.TaskResult, execErr error) api.TaskResult {
	if execErr == context.DeadlineExceeded {
		result.Status = "timeout"
		if strings.TrimSpace(result.Message) == "" {
			result.Message = execErr.Error()
		}
		return result
	}

	if strings.EqualFold(strings.TrimSpace(result.Status), "failed") {
		message := strings.ToLower(strings.TrimSpace(result.Message))
		if strings.Contains(message, "context deadline exceeded") ||
			strings.Contains(message, "timeout") ||
			strings.Contains(message, "timed out") {
			result.Status = "timeout"
		}
	}

	return result
}

func (a *Agent) registeredProtocols() []string {
	protocols := a.registry.Protocols()
	if len(protocols) == 0 {
		return []string{}
	}
	return protocols
}

func (a *Agent) currentHeartbeatInterval() time.Duration {
	if a.settings != nil {
		return a.settings.HeartbeatInterval()
	}
	return a.cfg.HeartbeatInterval()
}

func (a *Agent) currentTaskPollInterval() time.Duration {
	if a.settings != nil {
		return a.settings.TaskPollInterval()
	}
	return a.cfg.TaskPollInterval()
}

func (a *Agent) claimInterval() time.Duration {
	interval := a.currentTaskPollInterval()
	if interval <= 0 || interval > directClaimPollInterval {
		return directClaimPollInterval
	}
	return interval
}

func (a *Agent) recordHeartbeat(success bool) {
	if a.metrics != nil {
		a.metrics.IncHeartbeat(success)
	}
}

func (a *Agent) recordTaskExecution(status string) {
	if a.metrics != nil {
		a.metrics.IncTaskExecution(status)
	}
}

func (a *Agent) recordQueueDepth() {
	if a.metrics != nil {
		a.metrics.SetQueue(len(a.tasks), cap(a.tasks))
	}
}

func (a *Agent) setWorkerDelta(delta int) {
	if a.metrics != nil {
		a.metrics.WorkersDelta(delta)
	}
}

func (a *Agent) wait(ctx context.Context, d time.Duration) error {
	if d <= 0 {
		return nil
	}
	timer := time.NewTimer(d)
	defer timer.Stop()
	select {
	case <-ctx.Done():
		return ctx.Err()
	case <-timer.C:
		return nil
	}
}

func (a *Agent) flushCachedResults() {
	if a.cache == nil {
		return
	}
	go func() {
		flushCtx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
		defer cancel()
		_ = a.cache.Flush(flushCtx, func(ctx context.Context, result api.TaskResult) error {
			return a.submitTaskResult(ctx, result)
		})
	}()
}

func (a *Agent) submitResult(ctx context.Context, result api.TaskResult) {
	if result.Metadata == nil {
		result.Metadata = map[string]any{}
	}
	if !result.ScheduledAt.IsZero() {
		result.Metadata["scheduled_at"] = result.ScheduledAt.Format(time.RFC3339)
	}
	if err := a.submitTaskResult(ctx, result); err != nil {
		a.logger.Warn().Err(err).Str("task_id", result.TaskID).Msg("submit result failed")
		if a.cache != nil {
			a.cache.Enqueue(result)
		}
	} else {
		a.flushCachedResults()
	}
}

func (a *Agent) submitTaskResult(ctx context.Context, result api.TaskResult) error {
	if a.client != nil {
		if result.ScheduleID != "" {
			return a.client.SubmitScheduleResult(ctx, result)
		}
		return a.client.SubmitOneOffResult(ctx, result)
	}
	return a.transport.SubmitResult(ctx, result)
}

// Close releases transport resources.
func (a *Agent) Close() {
	if a.transport != nil {
		_ = a.transport.Close()
	}
}

func (a *Agent) startCommandLoop(ctx context.Context) {
	cmdCh := a.transport.Commands()
	if cmdCh == nil {
		return
	}
	go func() {
		for {
			select {
			case <-ctx.Done():
				return
			case cmd, ok := <-cmdCh:
				if !ok {
					return
				}
				a.handleCommand(ctx, cmd)
			}
		}
	}()
}

func (a *Agent) handleCommand(ctx context.Context, cmd transport.Command) {
	switch cmd.Name {
	case "config.refresh":
		if refresher, ok := a.settings.(interface {
			Sync(context.Context) error
		}); ok {
			if err := refresher.Sync(ctx); err != nil {
				a.logger.Warn().Err(err).Msg("config refresh command failed")
			} else {
				a.logger.Info().Msg("remote config refreshed via command")
			}
		}
	case "config.update":
		if cmd.ConfigUpdate != nil && a.scheduler != nil {
			a.scheduler.Apply(cmd.ConfigUpdate)
			a.logger.Info().
				Uint64("version", cmd.ConfigUpdate.GetVersion()).
				Int("schedules", len(cmd.ConfigUpdate.GetSchedules())).
				Msg("applied config update")
		} else {
			a.logger.Warn().Msg("config update command missing payload")
		}
	default:
		a.logger.Debug().Str("command", cmd.Name).Msg("command ignored")
	}
}

func (a *Agent) startMetricsReporter(ctx context.Context) {
	if a.metrics == nil || a.transport == nil {
		return
	}
	if os.Getenv("ONEALL_DISABLE_GRPC_METRICS_PUSH") == "1" {
		a.logger.Info().Msg("grpc metrics push disabled by env")
		return
	}
	ticker := time.NewTicker(metricsPushInterval)
	go func() {
		defer ticker.Stop()
		for {
			select {
			case <-ctx.Done():
				return
			case <-ticker.C:
				a.publishMetricsSnapshot(ctx)
			}
		}
	}()
}

func (a *Agent) publishMetricsSnapshot(ctx context.Context) {
	snapshot := a.metrics.Snapshot()
	payload := api.MetricsPayload{
		CapturedAt:    time.Now().UTC(),
		UptimeSeconds: snapshot.UptimeSeconds,
		CPUUsage:      snapshot.CPUUsagePercent,
		MemoryUsageMB: snapshot.MemoryUsageMB,
		Heartbeats: api.MetricsHeartbeat{
			Sent:        snapshot.Heartbeats.Sent,
			Failed:      snapshot.Heartbeats.Failed,
			LastSuccess: snapshot.Heartbeats.LastSuccess,
		},
		Tasks: api.MetricsTaskCounters{
			Fetched:  snapshot.Tasks.Fetched,
			Executed: snapshot.Tasks.Executed,
			Failed:   snapshot.Tasks.Failed,
		},
		Queue: api.MetricsQueueGauge{
			Depth:    snapshot.Queue.Depth,
			Capacity: snapshot.Queue.Capacity,
		},
		Workers: api.MetricsWorkerGauge{
			Active: snapshot.Workers.Active,
		},
	}
	if err := a.transport.PublishMetrics(ctx, payload); err != nil {
		a.logger.Debug().Err(err).Msg("failed to push metrics snapshot")
	}
}
