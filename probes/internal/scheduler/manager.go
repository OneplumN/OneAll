package scheduler

import (
	"context"
	"fmt"
	"os"
	"strconv"
	"sync"
	"time"

	"github.com/rs/zerolog"

	"github.com/one-pro/one-pro/probes/internal/api"
	gateway "github.com/one-pro/one-pro/probes/internal/probes/v1"
)

type Config struct {
	ID             string
	Target         string
	Protocol       string
	Interval       time.Duration
	TimeoutSeconds int
	StartAt        time.Time
	EndAt          *time.Time
	Metadata       map[string]any
	Paused         bool
	Version        uint64
}

type Manager struct {
	logger    zerolog.Logger
	taskQueue chan<- api.Task
	storage   Storage
	mu        sync.Mutex
	configs   map[string]*entry
	ticker    *time.Ticker
	drift     time.Duration
	version   uint64
}

type entry struct {
	cfg     Config
	nextRun time.Time
}

func NewManager(logger zerolog.Logger, taskQueue chan<- api.Task, storage Storage) *Manager {
	return &Manager{
		logger:    logger,
		taskQueue: taskQueue,
		storage:   storage,
		configs:   make(map[string]*entry),
		drift:     5 * time.Second,
	}
}

func (m *Manager) Start(ctx context.Context) {
	if m.storage != nil {
		if cfgs, version, err := m.storage.Load(); err == nil && len(cfgs) > 0 {
			m.logger.Info().Int("schedules", len(cfgs)).Msg("restored schedules from storage")
			m.restoreConfigs(cfgs, version)
		} else if err != nil && !os.IsNotExist(err) {
			m.logger.Warn().Err(err).Msg("failed to load scheduler storage")
		}
	}
	m.ticker = time.NewTicker(time.Second)
	go func() {
		for {
			select {
			case <-ctx.Done():
				m.ticker.Stop()
				return
			case <-m.ticker.C:
				m.tick()
			}
		}
	}()
}

func (m *Manager) Apply(update *gateway.ConfigUpdate) {
	if update == nil {
		return
	}
	m.mu.Lock()
	defer m.mu.Unlock()
	if update.GetFullResync() {
		m.configs = make(map[string]*entry)
	}
	for _, removed := range update.GetRemovedScheduleIds() {
		delete(m.configs, removed)
	}
	now := time.Now().UTC()
	for _, cfg := range update.GetSchedules() {
		conf := configFromProto(cfg)
		m.insertConfigLocked(conf, now)
	}
	m.version = update.GetVersion()
	m.persistLocked()
}

func (m *Manager) tick() {
	m.tickAt(time.Now().UTC())
}

func (m *Manager) tickAt(now time.Time) {
	m.mu.Lock()
	defer m.mu.Unlock()
	for _, ent := range m.configs {
		if ent.cfg.Paused {
			continue
		}
		if ent.cfg.EndAt != nil && now.After(*ent.cfg.EndAt) {
			continue
		}
		for !ent.nextRun.After(now) {
			scheduled := ent.nextRun
			ent.nextRun = ent.nextRun.Add(ent.cfg.Interval)
			m.logger.Info().
				Str("schedule", ent.cfg.ID).
				Str("protocol", ent.cfg.Protocol).
				Str("target", ent.cfg.Target).
				Time("scheduled_at", scheduled).
				Time("next_run", ent.nextRun).
				Msg("schedule due; queueing execution")
			m.enqueue(ent.cfg, scheduled, now)
		}
	}
}

func (m *Manager) enqueue(cfg Config, scheduled time.Time, now time.Time) {
	if now.Sub(scheduled) > m.drift {
		m.emitMissed(cfg, scheduled, fmt.Sprintf("missed schedule by %s", now.Sub(scheduled)))
		return
	}
	task := api.Task{
		ID:             scheduleTaskID(cfg.ID, scheduled),
		ScheduleID:     cfg.ID,
		Target:         cfg.Target,
		Protocol:       cfg.Protocol,
		TimeoutSeconds: cfg.TimeoutSeconds,
		ExpectStatus:   resolveExpectedStatus(cfg.Metadata),
		Metadata:       cloneMap(cfg.Metadata),
		ScheduledAt:    scheduled,
	}
	m.dispatchTask(task)
}

func scheduleTaskID(scheduleID string, at time.Time) string {
	return fmt.Sprintf("%s-%d", scheduleID, at.Unix())
}

func alignNext(start time.Time, interval time.Duration, now time.Time) time.Time {
	if interval <= 0 {
		return now
	}
	elapsed := now.Sub(start)
	steps := int64(elapsed / interval)
	if elapsed%interval != 0 {
		steps++
	}
	return start.Add(time.Duration(steps) * interval)
}

func cloneMap(src map[string]any) map[string]any {
	if src == nil {
		return map[string]any{}
	}
	dst := make(map[string]any, len(src))
	for k, v := range src {
		dst[k] = v
	}
	return dst
}

func (m *Manager) emitMissed(cfg Config, scheduled time.Time, reason string) {
	task := api.Task{
		ID:             scheduleTaskID(cfg.ID, scheduled),
		ScheduleID:     cfg.ID,
		Target:         cfg.Target,
		Protocol:       cfg.Protocol,
		TimeoutSeconds: cfg.TimeoutSeconds,
		ExpectStatus:   resolveExpectedStatus(cfg.Metadata),
		Metadata:       cloneMap(cfg.Metadata),
		ScheduledAt:    scheduled,
		Missed:         true,
	}
	task.Metadata["missed_reason"] = reason
	m.dispatchTask(task)
}

func (m *Manager) dispatchTask(task api.Task) {
	if m.taskQueue == nil {
		return
	}
	select {
	case m.taskQueue <- task:
		m.logger.Info().
			Str("task_id", task.ID).
			Str("schedule", task.ScheduleID).
			Str("protocol", task.Protocol).
			Str("target", task.Target).
			Time("scheduled_at", task.ScheduledAt).
			Msg("scheduler dispatched task")
	default:
		m.logger.Warn().
			Str("schedule", task.ScheduleID).
			Msg("task queue full, dropping execution")
	}
}

func (m *Manager) persistLocked() {
	if m.storage == nil {
		return
	}
	snapshot := make([]Config, 0, len(m.configs))
	for _, ent := range m.configs {
		snapshot = append(snapshot, cloneConfig(ent.cfg))
	}
	if err := m.storage.Save(snapshot, m.version); err != nil {
		m.logger.Warn().Err(err).Msg("failed to persist scheduler state")
	}
}

func (m *Manager) restoreConfigs(configs []Config, version uint64) {
	now := time.Now().UTC()
	m.mu.Lock()
	defer m.mu.Unlock()
	m.configs = make(map[string]*entry, len(configs))
	for _, cfg := range configs {
		m.insertConfigLocked(cfg, now)
	}
	m.version = version
}

func configFromProto(msg *gateway.ScheduleConfig) Config {
	interval := time.Duration(msg.GetIntervalSeconds())
	if interval <= 0 {
		interval = 60
	}
	interval *= time.Second
	start := time.Now().UTC()
	if msg.GetStartAt() != nil {
		start = msg.GetStartAt().AsTime().UTC()
	}
	cfg := Config{
		ID:             msg.GetScheduleId(),
		Target:         msg.GetTarget(),
		Protocol:       msg.GetProtocol(),
		Interval:       interval,
		TimeoutSeconds: int(msg.GetTimeoutSeconds()),
		StartAt:        start,
		Paused:         msg.GetPaused(),
		Version:        msg.GetVersion(),
		Metadata:       map[string]any{},
	}
	if msg.GetEndAt() != nil {
		end := msg.GetEndAt().AsTime().UTC()
		cfg.EndAt = &end
	}
	if msg.GetMetadata() != nil {
		cfg.Metadata = msg.GetMetadata().AsMap()
	}
	return cfg
}

func (m *Manager) insertConfigLocked(cfg Config, now time.Time) {
	if cfg.Metadata == nil {
		cfg.Metadata = map[string]any{}
	}
	nextRun := cfg.StartAt
	if nextRun.Before(now) {
		nextRun = alignNext(cfg.StartAt, cfg.Interval, now)
	}
	m.configs[cfg.ID] = &entry{
		cfg:     cfg,
		nextRun: nextRun,
	}
	m.logger.Info().
		Str("schedule", cfg.ID).
		Str("protocol", cfg.Protocol).
		Str("target", cfg.Target).
		Bool("paused", cfg.Paused).
		Time("start_at", cfg.StartAt).
		Time("next_run", nextRun).
		Dur("interval", cfg.Interval).
		Msg("scheduler loaded config")
}

func cloneConfig(cfg Config) Config {
	clone := cfg
	clone.Metadata = cloneMap(cfg.Metadata)
	return clone
}

func (m *Manager) configSnapshot() []Config {
	snapshot := make([]Config, 0, len(m.configs))
	for _, ent := range m.configs {
		snapshot = append(snapshot, ent.cfg)
	}
	return snapshot
}

func resolveExpectedStatus(metadata map[string]any) int {
	if len(metadata) == 0 {
		return 0
	}
	raw, ok := metadata["expected_status_codes"]
	if !ok {
		return 0
	}
	switch value := raw.(type) {
	case []any:
		return firstValidStatus(value)
	default:
		return normalizeStatusCode(value)
	}
}

func firstValidStatus(values []any) int {
	for _, item := range values {
		if code := normalizeStatusCode(item); code != 0 {
			return code
		}
	}
	return 0
}

func normalizeStatusCode(value any) int {
	var code int
	switch v := value.(type) {
	case int:
		code = v
	case int32:
		code = int(v)
	case int64:
		code = int(v)
	case float32:
		code = int(v)
	case float64:
		code = int(v)
	case uint:
		code = int(v)
	case uint32:
		code = int(v)
	case uint64:
		code = int(v)
	case string:
		parsed, err := strconv.Atoi(v)
		if err != nil {
			return 0
		}
		code = parsed
	default:
		return 0
	}
	if code < 100 || code > 599 {
		return 0
	}
	return code
}
