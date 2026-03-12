package main

import (
	"context"
	"flag"
	"fmt"
	"os"
	"os/signal"
	"path/filepath"
	"syscall"
	"time"

	"github.com/rs/zerolog"
	"github.com/rs/zerolog/log"

	"github.com/one-pro/one-pro/probes/internal/agent"
	"github.com/one-pro/one-pro/probes/internal/api"
	"github.com/one-pro/one-pro/probes/internal/config"
	"github.com/one-pro/one-pro/probes/internal/control"
	"github.com/one-pro/one-pro/probes/internal/metrics"
	certificateplugin "github.com/one-pro/one-pro/probes/internal/plugins/certificate"
	httpplugin "github.com/one-pro/one-pro/probes/internal/plugins/http"
	"github.com/one-pro/one-pro/probes/internal/plugins/registry"
	tcpplugin "github.com/one-pro/one-pro/probes/internal/plugins/tcp"
	wssplugin "github.com/one-pro/one-pro/probes/internal/plugins/wss"
	"github.com/one-pro/one-pro/probes/internal/scheduler"
	"github.com/one-pro/one-pro/probes/internal/storage"
	"github.com/one-pro/one-pro/probes/internal/transport"
	"github.com/one-pro/one-pro/probes/internal/updater"
)

func main() {
	var configPath string
	var debug bool
	flag.StringVar(&configPath, "config", "config.yaml", "Path to configuration file")
	flag.BoolVar(&debug, "debug", false, "Enable debug logging")
	flag.Parse()

	zerolog.TimeFieldFormat = time.RFC3339
	level := zerolog.InfoLevel
	if debug {
		level = zerolog.DebugLevel
	}
	log.Logger = log.Output(zerolog.ConsoleWriter{Out: os.Stdout}).Level(level)

	cfg, err := config.Load(configPath)
	if err != nil {
		log.Fatal().Err(err).Msg("failed to load config")
	}

	client, err := api.NewClient(cfg.APIBaseURL, cfg.NodeID, cfg.APIToken, cfg.RequestTimeout(), cfg.InsecureSkipTLS)
	if err != nil {
		log.Fatal().Err(err).Msg("failed to create api client")
	}

	reg := registry.New()
	httpplugin.Register(reg, cfg.RequestTimeout())
	certificateplugin.Register(reg, cfg.RequestTimeout())
	tcpplugin.Register(reg, cfg.RequestTimeout())
	wssplugin.Register(reg, cfg.RequestTimeout())

	updateSvc := updater.NewService(cfg.UpdateDir, log.Logger)
	settings := control.NewManager(cfg, client, log.Logger, updateSvc)
	if err := settings.Sync(context.Background()); err != nil {
		log.Warn().Err(err).Msg("failed to synchronize remote config")
	}

	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
	defer stop()

	if !cfg.UseGRPC() {
		log.Fatal().Msg("grpc_gateway must be configured; REST transport has been removed")
	}
	trans, err := transport.NewGRPCTransport(ctx, cfg, reg.Protocols(), log.Logger)
	if err != nil {
		log.Fatal().Err(err).Msg("failed to initialize grpc transport")
	}

	recorder := metrics.NewRecorder()
	var cache *storage.ResultCache
	if cfg.ResultCachePath != "" {
		cache = storage.NewResultCache(cfg.ResultCachePath, cfg.ResultCacheLimit, log.Logger)
	}
	storePath := resolveScheduleStorePath(cfg)
	log.Info().Str("schedule_store", storePath).Msg("using schedule storage")
	scheduleStore := scheduler.NewJSONStorage(storePath)
	ag := agent.New(cfg, client, reg, log.Logger, recorder, settings, cache, trans, scheduleStore)
	defer ag.Close()

	go settings.Run(ctx)
	if cfg.MetricsAddr != "" {
		_ = metrics.Serve(ctx, cfg.MetricsAddr, recorder, log.Logger)
	}

	if err := ag.Run(ctx); err != nil && err != context.Canceled {
		fmt.Fprintf(os.Stderr, "agent stopped: %v\n", err)
		os.Exit(1)
	}
}

func resolveScheduleStorePath(cfg config.Config) string {
	if cfg.ScheduleStorePath != "" {
		return cfg.ScheduleStorePath
	}
	if cfg.ResultCachePath != "" {
		return filepath.Join(filepath.Dir(cfg.ResultCachePath), "schedules.json")
	}
	if dir, err := os.UserConfigDir(); err == nil && dir != "" {
		return filepath.Join(dir, "oneall", "schedules.json")
	}
	return "schedules.json"
}
