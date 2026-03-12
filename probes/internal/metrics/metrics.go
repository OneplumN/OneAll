package metrics

import (
	"context"
	"encoding/json"
	"errors"
	"net/http"
	"sync/atomic"
	"time"

	"github.com/rs/zerolog"
)

// Recorder captures probe runtime counters for observability.
type Recorder struct {
	startedAt time.Time
	heartbeatsSent   atomic.Int64
	heartbeatsFailed atomic.Int64
	lastHeartbeatSuccess atomic.Value
	tasksFetched atomic.Int64
	tasksExecuted atomic.Int64
	tasksFailed   atomic.Int64
	queueDepth    atomic.Int64
	queueCapacity atomic.Int64
	activeWorkers atomic.Int64
}

// Snapshot represents metrics payload served to HTTP clients.
type Snapshot struct {
	StartTime     time.Time `json:"start_time"`
	UptimeSeconds int64     `json:"uptime_seconds"`
	Heartbeats    struct {
		Sent        int64     `json:"sent"`
		Failed      int64     `json:"failed"`
		LastSuccess *time.Time `json:"last_success,omitempty"`
	} `json:"heartbeats"`
	Tasks struct {
		Fetched  int64 `json:"fetched"`
		Executed int64 `json:"executed"`
		Failed   int64 `json:"failed"`
	} `json:"tasks"`
	Queue struct {
		Depth    int64 `json:"depth"`
		Capacity int64 `json:"capacity"`
	} `json:"queue"`
	Workers struct {
		Active int64 `json:"active"`
	} `json:"workers"`
}

// NewRecorder instantiates an empty metrics recorder.
func NewRecorder() *Recorder {
	r := &Recorder{startedAt: time.Now()}
	return r
}

// IncHeartbeat records a heartbeat attempt outcome.
func (r *Recorder) IncHeartbeat(success bool) {
	r.heartbeatsSent.Add(1)
	if success {
		now := time.Now()
		r.lastHeartbeatSuccess.Store(now)
		return
	}
	r.heartbeatsFailed.Add(1)
}

// IncTasksFetched adds fetched task count.
func (r *Recorder) IncTasksFetched(count int) {
	if count <= 0 {
		return
	}
	r.tasksFetched.Add(int64(count))
}

// IncTaskExecution records executed task status.
func (r *Recorder) IncTaskExecution(status string) {
	r.tasksExecuted.Add(1)
	if status != "success" {
		r.tasksFailed.Add(1)
	}
}

// SetQueue updates queue depth/capacity gauges.
func (r *Recorder) SetQueue(depth, capacity int) {
	r.queueDepth.Store(int64(depth))
	r.queueCapacity.Store(int64(capacity))
}

// WorkersDelta increments/decrements active worker count.
func (r *Recorder) WorkersDelta(delta int) {
	r.activeWorkers.Add(int64(delta))
}

// Snapshot returns the current metrics snapshot.
func (r *Recorder) Snapshot() Snapshot {
	s := Snapshot{
		StartTime:     r.startedAt,
		UptimeSeconds: int64(time.Since(r.startedAt).Seconds()),
	}
	s.Heartbeats.Sent = r.heartbeatsSent.Load()
	s.Heartbeats.Failed = r.heartbeatsFailed.Load()
	if value := r.lastHeartbeatSuccess.Load(); value != nil {
		if ts, ok := value.(time.Time); ok {
			s.Heartbeats.LastSuccess = &ts
		}
	}
	s.Tasks.Fetched = r.tasksFetched.Load()
	s.Tasks.Executed = r.tasksExecuted.Load()
	s.Tasks.Failed = r.tasksFailed.Load()
	s.Queue.Depth = r.queueDepth.Load()
	s.Queue.Capacity = r.queueCapacity.Load()
	s.Workers.Active = r.activeWorkers.Load()
	return s
}

// Serve launches an HTTP server exposing metrics until ctx is cancelled.
func Serve(ctx context.Context, addr string, recorder *Recorder, logger zerolog.Logger) error {
	if addr == "" || recorder == nil {
		return nil
	}
	mux := http.NewServeMux()
	mux.HandleFunc("/probe/metrics", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		if err := json.NewEncoder(w).Encode(recorder.Snapshot()); err != nil {
			w.WriteHeader(http.StatusInternalServerError)
		}
	})
	srv := &http.Server{Addr: addr, Handler: mux}
	go func() {
		<-ctx.Done()
		shutdownCtx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		_ = srv.Shutdown(shutdownCtx)
	}()
	go func() {
		if err := srv.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
			logger.Error().Err(err).Str("addr", addr).Msg("metrics server stopped")
		}
	}()
	return nil
}
