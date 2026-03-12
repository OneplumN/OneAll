package scheduler

import (
	"encoding/json"
	"os"
	"path/filepath"
)

type JSONStorage struct {
	path string
}

type snapshot struct {
	Version uint64   `json:"version"`
	Configs []Config `json:"configs"`
}

func NewJSONStorage(path string) *JSONStorage {
	return &JSONStorage{path: path}
}

func (s *JSONStorage) Load() ([]Config, uint64, error) {
	data, err := os.ReadFile(s.path)
	if err != nil {
		return nil, 0, err
	}
	var snap snapshot
	if err := json.Unmarshal(data, &snap); err != nil {
		return nil, 0, err
	}
	return snap.Configs, snap.Version, nil
}

func (s *JSONStorage) Save(configs []Config, version uint64) error {
	tmp := s.path + ".tmp"
	if err := os.MkdirAll(filepath.Dir(s.path), 0o755); err != nil {
		return err
	}
	data, err := json.MarshalIndent(snapshot{Version: version, Configs: configs}, "", "  ")
	if err != nil {
		return err
	}
	if err := os.WriteFile(tmp, data, 0o600); err != nil {
		return err
	}
	return os.Rename(tmp, s.path)
}
