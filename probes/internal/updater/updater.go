package updater

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"errors"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"time"

	"github.com/rs/zerolog"

	"github.com/one-pro/one-pro/probes/internal/api"
)

// Service downloads and stages agent updates.
type Service struct {
	dir     string
	logger  zerolog.Logger
	http    *http.Client
	mu      sync.Mutex
	version string
}

// NewService creates a new updater writing files to dir.
func NewService(dir string, logger zerolog.Logger) *Service {
	if dir == "" {
		return nil
	}
	client := &http.Client{Timeout: 2 * time.Minute}
	return &Service{dir: dir, logger: logger, http: client}
}

// Apply downloads the update instruction if not already staged.
func (s *Service) Apply(ctx context.Context, instruction *api.UpdateInstruction) {
	if s == nil || instruction == nil || instruction.DownloadURL == "" || instruction.Version == "" {
		return
	}
	s.mu.Lock()
	if instruction.Version == s.version {
		s.mu.Unlock()
		return
	}
	s.mu.Unlock()
	if err := s.download(ctx, instruction); err != nil {
		s.logger.Warn().Err(err).Str("version", instruction.Version).Msg("update download failed")
		return
	}
	s.mu.Lock()
	s.version = instruction.Version
	s.mu.Unlock()
}

func (s *Service) download(ctx context.Context, instruction *api.UpdateInstruction) error {
	if err := os.MkdirAll(s.dir, 0o755); err != nil {
		return err
	}
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, instruction.DownloadURL, nil)
	if err != nil {
		return err
	}
	resp, err := s.http.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("download status %d", resp.StatusCode)
	}
	tmp, err := os.CreateTemp(s.dir, "update-*.bin")
	if err != nil {
		return err
	}
	defer os.Remove(tmp.Name())
	defer tmp.Close()
	hasher := sha256.New()
	if _, err := io.Copy(io.MultiWriter(tmp, hasher), resp.Body); err != nil {
		return err
	}
	if err := tmp.Sync(); err != nil {
		return err
	}
	digest := hex.EncodeToString(hasher.Sum(nil))
	if expected := normalizeHash(instruction.SHA256); expected != "" && expected != digest {
		return errors.New("checksum mismatch")
	}
	filename := filepath.Join(s.dir, fmt.Sprintf("oneall-probe-%s", instruction.Version))
	if err := os.Chmod(tmp.Name(), 0o755); err != nil {
		return err
	}
	if err := os.Rename(tmp.Name(), filename); err != nil {
		return err
	}
	s.logger.Info().Str("version", instruction.Version).Str("path", filename).Msg("update downloaded")
	s.logger.Info().Str("path", filename).Msg("请在维护窗口将该二进制替换正在运行的探针或配合 systemd ExecStart 配置实现自更新")
	return nil
}

func normalizeHash(value string) string {
	return strings.ToLower(strings.TrimSpace(value))
}

// ManualTrigger downloads the provided instruction immediately.
func (s *Service) ManualTrigger(url, version, sha string) error {
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Minute)
	defer cancel()
	instruction := api.UpdateInstruction{Version: version, DownloadURL: url, SHA256: sha}
	return s.download(ctx, &instruction)
}

