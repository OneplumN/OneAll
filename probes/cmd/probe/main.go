package main

import (
	"context"
	"flag"
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
	"github.com/one-pro/one-pro/probes/internal/system"
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

	// Apply any persisted node credentials from state file.
	statePath := config.StatePath(cfg, configPath)
	if err := config.LoadState(statePath, &cfg); err != nil {
		log.Warn().Err(err).Str("state_path", statePath).Msg("failed to load probe state")
	}

	host := system.Collect()
	reg := registry.New()
	httpplugin.Register(reg, cfg.RequestTimeout())
	certificateplugin.Register(reg, cfg.RequestTimeout())
	tcpplugin.Register(reg, cfg.RequestTimeout())
	wssplugin.Register(reg, cfg.RequestTimeout())

	// If node credentials are still missing, perform one-time registration.
	// 是否需要引导 token 由服务端的 PROBE_BOOTSTRAP_TOKEN 决定：
	// - 未配置时：后端放行，开发环境下零配置自动注册；
	// - 已配置时：如果在配置文件中提供 bootstrap_token，这里会随请求一起发送。
	if cfg.NodeID == "" || cfg.APIToken == "" {
		ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
		defer cancel()
		regPayload := api.RegistrationPayload{
			Hostname:           host.Hostname,
			IPAddress:          host.IP,
			Location:           cfg.Location,
			NetworkType:        cfg.NetworkType,
			SupportedProtocols: reg.Protocols(),
			AgentVersion:       "go-probe",
		}
		resp, err := api.RegisterProbe(ctx, cfg, regPayload)
		if err != nil {
			log.Fatal().Err(err).Msg("probe registration failed")
		}
		cfg.NodeID = resp.NodeID
		cfg.APIToken = resp.APIToken
		if err := config.PersistState(statePath, cfg); err != nil {
			log.Warn().Err(err).Str("state_path", statePath).Msg("failed to persist probe state")
		}
		log.Info().
			Str("node_id", cfg.NodeID).
			Str("location", resp.Location).
			Str("network_type", resp.NetworkType).
			Msg("probe registered successfully")
	}

	client, err := api.NewClient(cfg.APIBaseURL, cfg.NodeID, cfg.APIToken, cfg.RequestTimeout(), cfg.InsecureSkipTLS)
	if err != nil {
		log.Fatal().Err(err).Msg("failed to create api client")
	}

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
	go settings.Run(ctx)
	if cfg.MetricsAddr != "" {
		if err := metrics.Serve(ctx, cfg.MetricsAddr, recorder, log.Logger); err != nil {
			log.Error().Err(err).Str("addr", cfg.MetricsAddr).Msg("failed to start metrics server")
		}
	}

	// 运行 agent 主循环；当心跳等 gRPC 通道出现连接级错误时，允许自动重试重建连接。
	for {
		select {
		case <-ctx.Done():
			return
		default:
		}

		ag := agent.New(cfg, client, reg, log.Logger, recorder, settings, cache, trans, scheduleStore)
		if err := ag.Run(ctx); err != nil && err != context.Canceled {
			log.Error().Err(err).Msg("agent run exited with error; will attempt reconnect after backoff")
			ag.Close()
			// 简单退避后重连 gRPC。
			select {
			case <-ctx.Done():
				return
			case <-time.After(10 * time.Second):
			}
			newTrans, err := transport.NewGRPCTransport(ctx, cfg, reg.Protocols(), log.Logger)
			if err != nil {
				log.Error().Err(err).Msg("failed to re-establish grpc transport; backing off")
				// 如果重连失败，继续等待并重试。
				continue
			}
			trans = newTrans
			continue
		}

		// 正常退出或被取消，直接返回。
		ag.Close()
		return
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
