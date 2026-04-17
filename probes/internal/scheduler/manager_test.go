package scheduler

import (
	"testing"
	"time"

	"github.com/rs/zerolog"

	"github.com/one-pro/one-pro/probes/internal/api"
)

func TestResolveExpectedStatus(t *testing.T) {
	tests := []struct {
		name string
		meta map[string]any
		want int
	}{
		{
			name: "nil metadata",
			meta: nil,
			want: 0,
		},
		{
			name: "slice of floats",
			meta: map[string]any{
				"expected_status_codes": []any{float64(404), float64(200)},
			},
			want: 404,
		},
		{
			name: "string value",
			meta: map[string]any{
				"expected_status_codes": []any{"503", "200"},
			},
			want: 503,
		},
		{
			name: "single int",
			meta: map[string]any{
				"expected_status_codes": 302,
			},
			want: 302,
		},
		{
			name: "invalid values",
			meta: map[string]any{
				"expected_status_codes": []any{"abc", float64(50)},
			},
			want: 0,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := resolveExpectedStatus(tt.meta); got != tt.want {
				t.Fatalf("resolveExpectedStatus() = %d, want %d", got, tt.want)
			}
		})
	}
}

func TestManagerDispatchesFutureScheduleWhenDue(t *testing.T) {
	t.Parallel()

	taskQueue := make(chan api.Task, 1)
	manager := NewManager(zerolog.Nop(), taskQueue, nil)
	now := time.Now().UTC()
	cfg := Config{
		ID:             "schedule-1",
		Target:         "https://example.com",
		Protocol:       "HTTPS",
		Interval:       5 * time.Minute,
		TimeoutSeconds: 5,
		StartAt:        now.Add(10 * time.Second),
		Metadata:       map[string]any{"expected_status_codes": []any{float64(200)}},
	}

	manager.mu.Lock()
	manager.insertConfigLocked(cfg, now)
	manager.mu.Unlock()

	manager.tickAt(cfg.StartAt)

	select {
	case task := <-taskQueue:
		if task.ScheduleID != cfg.ID {
			t.Fatalf("task schedule id = %s, want %s", task.ScheduleID, cfg.ID)
		}
		if !task.ScheduledAt.Equal(cfg.StartAt) {
			t.Fatalf("task scheduled_at = %s, want %s", task.ScheduledAt, cfg.StartAt)
		}
	default:
		t.Fatal("expected scheduler to dispatch task")
	}
}
