package storage

import (
	"context"
	"encoding/json"
	"errors"
	"os"
	"path/filepath"
	"sync"

	"github.com/rs/zerolog"

	"github.com/one-pro/one-pro/probes/internal/api"
)

// ResultCache persists task results that failed to submit.
type ResultCache struct {
	path  string
	limit int
	mu    sync.Mutex
	log   zerolog.Logger
}

// NewResultCache creates a cache at the given path.
func NewResultCache(path string, limit int, logger zerolog.Logger) *ResultCache {
	if limit <= 0 {
		limit = 100
	}
	return &ResultCache{path: path, limit: limit, log: logger}
}

// Enqueue stores a failed result for later retry.
func (c *ResultCache) Enqueue(result api.TaskResult) {
	if c == nil || c.path == "" {
		return
	}
	c.mu.Lock()
	defer c.mu.Unlock()
	entries := c.load()
	entries = append(entries, result)
	if len(entries) > c.limit {
		entries = entries[len(entries)-c.limit:]
	}
	c.save(entries)
}

// Flush attempts to resubmit cached results via the provided submit function.
func (c *ResultCache) Flush(ctx context.Context, submit func(context.Context, api.TaskResult) error) error {
	if c == nil || c.path == "" {
		return nil
	}
	c.mu.Lock()
	defer c.mu.Unlock()
	entries := c.load()
	if len(entries) == 0 {
		return nil
	}
	remaining := make([]api.TaskResult, 0, len(entries))
	for _, entry := range entries {
		if ctx.Err() != nil {
			remaining = append(remaining, entry)
			continue
		}
		if err := submit(ctx, entry); err != nil {
			c.log.Warn().Err(err).Str("task_id", entry.TaskID).Msg("flush cached result failed")
			remaining = append(remaining, entry)
			break
		}
	}
	if len(remaining) == len(entries) {
		return nil
	}
	return c.save(remaining)
}

func (c *ResultCache) load() []api.TaskResult {
	if c.path == "" {
		return nil
	}
	data, err := os.ReadFile(c.path)
	if err != nil {
		return nil
	}
	var entries []api.TaskResult
	if err := json.Unmarshal(data, &entries); err != nil {
		c.log.Warn().Err(err).Msg("failed to read result cache")
		return nil
	}
	return entries
}

func (c *ResultCache) save(entries []api.TaskResult) error {
	if c.path == "" {
		return errors.New("cache path not configured")
	}
	if err := os.MkdirAll(filepath.Dir(c.path), 0o755); err != nil {
		return err
	}
	data, err := json.Marshal(entries)
	if err != nil {
		return err
	}
	return os.WriteFile(c.path, data, 0o600)
}

