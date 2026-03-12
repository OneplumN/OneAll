package control

import (
	"context"
	"sync/atomic"
	"time"

	"github.com/rs/zerolog"

	"github.com/one-pro/one-pro/probes/internal/api"
	"github.com/one-pro/one-pro/probes/internal/config"
	"github.com/one-pro/one-pro/probes/internal/updater"
)

// RemoteConfig represents override settings fetched from the controller.
type RemoteConfig struct {
	Version             string   `json:"version"`
	HeartbeatInterval   int      `json:"heartbeat_interval"`
	TaskPollInterval    int      `json:"task_poll_interval"`
	MaxConcurrentTasks  int      `json:"max_concurrent_tasks"`
	EnabledProtocols    []string `json:"enabled_protocols"`
	LogLevel            string   `json:"log_level"`
}

// Settings exposes the resolved runtime configuration values.
type Settings interface {
	HeartbeatInterval() time.Duration
	TaskPollInterval() time.Duration
	MaxConcurrency() int
}

// Manager keeps track of remote config overrides.
type Manager struct {
	client        *api.Client
	logger        zerolog.Logger
	pollInterval  time.Duration
	fallbackHB    time.Duration
	fallbackPoll  time.Duration
	fallbackSlots int
	heartbeatMs   atomic.Int64
	taskPollMs    atomic.Int64
	maxSlots      atomic.Int64
	lastVersion   atomic.Value
	updater       *updater.Service
}

// NewManager constructs a manager from local config.
func NewManager(cfg config.Config, client *api.Client, logger zerolog.Logger, upd *updater.Service) *Manager {
	mgr := &Manager{
		client:        client,
		logger:        logger,
		pollInterval:  60 * time.Second,
		fallbackHB:    cfg.HeartbeatInterval(),
		fallbackPoll:  cfg.TaskPollInterval(),
		fallbackSlots: cfg.MaxConcurrency(),
		updater:       upd,
	}
	mgr.heartbeatMs.Store(millis(cfg.HeartbeatInterval()))
	mgr.taskPollMs.Store(millis(cfg.TaskPollInterval()))
	mgr.maxSlots.Store(int64(cfg.MaxConcurrency()))
	return mgr
}

// Sync fetches the latest remote config once.
func (m *Manager) Sync(ctx context.Context) error {
	return m.fetchAndApply(ctx)
}

// Run polls remote config periodically until context is cancelled.
func (m *Manager) Run(ctx context.Context) {
	ticker := time.NewTicker(m.pollInterval)
	defer ticker.Stop()
	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			if err := m.fetchAndApply(ctx); err != nil {
				m.logger.Warn().Err(err).Msg("failed to refresh remote config")
			}
		}
	}
}

// HeartbeatInterval returns the current heartbeat interval.
func (m *Manager) HeartbeatInterval() time.Duration {
	return durationOrFallback(m.heartbeatMs.Load(), m.fallbackHB)
}

// TaskPollInterval returns the current task polling interval.
func (m *Manager) TaskPollInterval() time.Duration {
	return durationOrFallback(m.taskPollMs.Load(), m.fallbackPoll)
}

// MaxConcurrency returns max concurrent tasks.
func (m *Manager) MaxConcurrency() int {
	value := m.maxSlots.Load()
	if value <= 0 {
		return m.fallbackSlots
	}
	return int(value)
}

func (m *Manager) fetchAndApply(ctx context.Context) error {
	if m.client == nil {
		return nil
	}
	config, err := m.client.FetchRemoteConfig(ctx)
	if err != nil {
		return err
	}
	m.apply(config)
	return nil
}

func (m *Manager) apply(remote api.RemoteConfigResponse) {
	if remote.HeartbeatInterval > 0 {
		m.heartbeatMs.Store(int64(remote.HeartbeatInterval) * 1000)
	}
	if remote.TaskPollInterval > 0 {
		m.taskPollMs.Store(int64(remote.TaskPollInterval) * 1000)
	}
	if remote.MaxConcurrentTasks > 0 {
		m.maxSlots.Store(int64(remote.MaxConcurrentTasks))
	}
	prev, _ := m.lastVersion.Load().(string)
	if remote.Version != "" && remote.Version != prev {
		m.logger.Info().Str("version", remote.Version).Msg("remote config applied")
		m.lastVersion.Store(remote.Version)
	}
	m.scheduleUpdate(remote.Update)
}

func (m *Manager) scheduleUpdate(update *api.UpdateInstruction) {
	if update == nil || m.updater == nil {
		return
	}
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Minute)
	go func() {
		defer cancel()
		m.updater.Apply(ctx, update)
	}()
}

func millis(d time.Duration) int64 {
	if d <= 0 {
		return 0
	}
	return d.Milliseconds()
}

func durationOrFallback(value int64, fallback time.Duration) time.Duration {
	if value <= 0 {
		return fallback
	}
	return time.Duration(value) * time.Millisecond
}
