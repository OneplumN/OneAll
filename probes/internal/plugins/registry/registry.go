package registry

import (
	"context"
	"fmt"
	"sort"
	"strings"
	"sync"

	"github.com/one-pro/one-pro/probes/internal/api"
)

// Plugin describes a detection implementation for a specific protocol.
type Plugin interface {
	Protocols() []string
	Execute(ctx context.Context, task api.Task) (api.TaskResult, error)
}

// Registry holds protocol to plugin mappings.
type Registry struct {
	mu      sync.RWMutex
	plugins map[string]Plugin
}

// New returns an empty registry.
func New() *Registry {
	return &Registry{plugins: make(map[string]Plugin)}
}

// Register stores a plugin for all of its declared protocols.
func (r *Registry) Register(p Plugin) {
	r.mu.Lock()
	defer r.mu.Unlock()
	for _, proto := range p.Protocols() {
		key := strings.ToUpper(proto)
		r.plugins[key] = p
	}
}

// Get retrieves the plugin for the provided protocol.
func (r *Registry) Get(protocol string) (Plugin, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()
	key := strings.ToUpper(protocol)
	plugin, ok := r.plugins[key]
	if !ok {
		return nil, fmt.Errorf("no plugin registered for protocol %s", protocol)
	}
	return plugin, nil
}

// Protocols returns the registered protocol identifiers.
func (r *Registry) Protocols() []string {
	r.mu.RLock()
	defer r.mu.RUnlock()
	protocols := make([]string, 0, len(r.plugins))
	for proto := range r.plugins {
		protocols = append(protocols, proto)
	}
	sort.Strings(protocols)
	return protocols
}
