package transport

import (
	"context"
	"crypto/tls"
	"crypto/x509"
	"errors"
	"fmt"
	"os"
	"sync"
	"time"

	"github.com/rs/zerolog"
	"google.golang.org/grpc"
	"google.golang.org/grpc/backoff"
	"google.golang.org/grpc/connectivity"
	"google.golang.org/grpc/credentials"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/grpc/keepalive"
	"google.golang.org/protobuf/types/known/structpb"
	"google.golang.org/protobuf/types/known/timestamppb"

	"github.com/one-pro/one-pro/probes/internal/api"
	"github.com/one-pro/one-pro/probes/internal/config"
	gateway "github.com/one-pro/one-pro/probes/internal/probes/v1"
)

// GRPCTransport implements the transport interface over a gRPC bidirectional stream.
type GRPCTransport struct {
	cfg        config.Config
	logger     zerolog.Logger
	protocols  []string
	baseCtx    context.Context
	baseCancel context.CancelFunc
	conn       *grpc.ClientConn
	client     gateway.ProbeGatewayClient
	stream     gateway.ProbeGateway_ConnectClient
	sendMu     sync.Mutex
	tasks      chan api.Task
	cancelFunc context.CancelFunc
	commands   chan Command
}

// NewGRPCTransport establishes a streaming connection to the controller.
func NewGRPCTransport(ctx context.Context, cfg config.Config, protocols []string, logger zerolog.Logger) (*GRPCTransport, error) {
	if cfg.GRPCGateway == "" {
		return nil, errors.New("grpc gateway address required")
	}
	baseCtx, baseCancel := context.WithCancel(ctx)
	dialCtx, cancel := context.WithTimeout(baseCtx, 10*time.Second)
	defer cancel()

	dialOpt, err := buildDialCredentials(cfg)
	if err != nil {
		return nil, err
	}

	conn, err := grpc.DialContext(
		dialCtx,
		cfg.GRPCGateway,
		dialOpt,
		grpc.WithBlock(),
		grpc.WithConnectParams(grpc.ConnectParams{
			Backoff: backoff.Config{
				BaseDelay:  time.Second,
				Multiplier: 1.6,
				Jitter:     0.2,
				MaxDelay:   10 * time.Second,
			},
			MinConnectTimeout: 10 * time.Second,
		}),
		grpc.WithKeepaliveParams(keepalive.ClientParameters{
			// Application-level heartbeats are sent every 30s, so transport keepalive
			// only needs to catch very long idle periods. A 120s ping cadence was
			// strongly correlated with stream resets in local debugging.
			Time:                10 * time.Minute,
			Timeout:             20 * time.Second,
			PermitWithoutStream: true,
		}),
	)
	if err != nil {
		return nil, err
	}

	client := gateway.NewProbeGatewayClient(conn)
	t := &GRPCTransport{
		cfg:        cfg,
		logger:     logger,
		protocols:  protocols,
		baseCtx:    baseCtx,
		baseCancel: baseCancel,
		conn:       conn,
		client:     client,
		tasks:      make(chan api.Task, 128),
		commands:   make(chan Command, 16),
	}
	if err := t.reconnectStream(); err != nil {
		t.Close()
		return nil, err
	}
	go t.readLoop()
	return t, nil
}

func (t *GRPCTransport) sendHello() error {
	msg := &gateway.ProbeMessage{
		Body: &gateway.ProbeMessage_Hello{
			Hello: &gateway.ProbeHello{
				ProbeId:            t.cfg.NodeID,
				Token:              t.cfg.APIToken,
				SupportedProtocols: append([]string{}, t.protocols...),
				MaxConcurrency:     uint32(t.cfg.MaxConcurrency()),
				AgentVersion:       "go-probe",
			},
		},
	}
	return t.send(msg)
}

func (t *GRPCTransport) readLoop() {
	defer close(t.commands)
	for {
		stream := t.currentStream()
		if stream == nil {
			if t.baseCtx.Err() != nil {
				return
			}
			if err := t.reconnectStream(); err != nil {
				t.logger.Warn().Err(err).Msg("grpc stream reconnect aborted")
				return
			}
			continue
		}

		response, err := stream.Recv()
		if err != nil {
			if t.baseCtx.Err() != nil {
				return
			}
			t.logger.Warn().
				Err(err).
				Str("connection_state", t.connectionState()).
				Msg("grpc stream receive failed")
			if reconnectErr := t.reconnectStream(); reconnectErr != nil {
				t.logger.Warn().Err(reconnectErr).Msg("grpc stream reconnect failed")
				return
			}
			continue
		}
		switch response.Body.(type) {
		case *gateway.ServerMessage_Task:
			task := response.GetTask()
			if task == nil {
				continue
			}
			apiTask := api.Task{
				ID:             task.TaskId,
				ScheduleID:     task.ScheduleId,
				Protocol:       task.Protocol,
				Target:         task.Target,
				TimeoutSeconds: int(task.TimeoutSeconds),
			}
			if task.Metadata != nil {
				apiTask.Metadata = task.Metadata.AsMap()
			}
			if len(task.ExpectedStatusCodes) > 0 {
				apiTask.ExpectStatus = int(task.ExpectedStatusCodes[0])
			}
			select {
			case t.tasks <- apiTask:
			default:
				t.logger.Warn().Msg("task buffer full, dropping task")
			}
		case *gateway.ServerMessage_Ack:
			ack := response.GetAck()
			t.logger.Info().
				Str("probe", ack.GetProbeId()).
				Uint32("heartbeat_interval", ack.GetHeartbeatIntervalSeconds()).
				Msg("received probe gateway ack")
		case *gateway.ServerMessage_Command:
			cmd := response.GetCommand()
			if cmd == nil {
				continue
			}
			command := Command{Name: cmd.Command}
			if payload := cmd.Payload; payload != nil {
				command.Payload = payload.AsMap()
			}
			select {
			case t.commands <- command:
			default:
				t.logger.Warn().Msg("command buffer full, dropping instruction")
			}
		case *gateway.ServerMessage_ConfigUpdate:
			update := response.GetConfigUpdate()
			if update == nil {
				continue
			}
			t.handleConfigUpdate(update)
		default:
			// ignore commands for now
		}
	}
}

func (t *GRPCTransport) SendHeartbeat(ctx context.Context, payload api.HeartbeatRequest) error {
	// 优先上传“内存使用率（百分比）”而不是绝对 MB 数。
	// 为了兼容旧逻辑，如果百分比不存在，则退回到 MB。
	memPct, ok := payload.Metrics["memory_usage_pct"]
	if !ok {
		memPct = payload.Metrics["memory_usage_mb"]
	}
	heartbeat := &gateway.Heartbeat{
		SentAt:        timestamppb.New(payload.SentAt),
		Status:        payload.Status,
		CpuUsage:      payload.Metrics["cpu_usage"],
		MemoryUsageMb: memPct,
		QueueDepth:    uint32(payload.Metrics["queue_depth"]),
		ActiveTasks:   uint32(payload.Metrics["active_tasks"]),
		IpAddress:     payload.IPAddress,
	}
	return t.send(&gateway.ProbeMessage{
		Body: &gateway.ProbeMessage_Heartbeat{Heartbeat: heartbeat},
	})
}

func (t *GRPCTransport) FetchTasks(ctx context.Context, limit int) ([]api.Task, error) {
	if limit <= 0 {
		limit = 1
	}
	request := &gateway.ProbeMessage{
		Body: &gateway.ProbeMessage_TaskRequest{
			TaskRequest: &gateway.TaskPullRequest{Limit: uint32(limit)},
		},
	}
	if err := t.send(request); err != nil {
		return nil, err
	}

	collected := make([]api.Task, 0, limit)
	timer := time.NewTimer(500 * time.Millisecond)
	defer timer.Stop()

	for len(collected) < limit {
		select {
		case task, ok := <-t.tasks:
			if !ok {
				return collected, errors.New("task channel closed")
			}
			collected = append(collected, task)
			if len(collected) >= limit {
				return collected, nil
			}
			if !timer.Stop() {
				select {
				case <-timer.C:
				default:
				}
			}
			timer.Reset(200 * time.Millisecond)
		case <-ctx.Done():
			return collected, ctx.Err()
		case <-timer.C:
			return collected, nil
		}
	}
	return collected, nil
}

func (t *GRPCTransport) SubmitResult(ctx context.Context, result api.TaskResult) error {
	payload := &gateway.TaskResult{
		TaskId:         result.TaskID,
		ScheduleId:     result.ScheduleID,
		Protocol:       result.Protocol,
		Status:         result.Status,
		Message:        result.Message,
		ResponseTimeMs: uint32(result.LatencyMs),
		StatusCode:     uint32(result.StatusCode),
	}
	if len(result.Metadata) > 0 {
		if meta, err := structpb.NewStruct(result.Metadata); err == nil {
			payload.Metadata = meta
		}
	}
	if !result.ScheduledAt.IsZero() {
		payload.ScheduledAt = timestamppb.New(result.ScheduledAt)
	}
	if !result.FinishedAt.IsZero() {
		payload.FinishedAt = timestamppb.New(result.FinishedAt)
	}
	return t.send(&gateway.ProbeMessage{
		Body: &gateway.ProbeMessage_Result{Result: payload},
	})
}

func (t *GRPCTransport) PublishMetrics(ctx context.Context, payload api.MetricsPayload) error {
	metrics := &gateway.RuntimeMetrics{
		UptimeSeconds: uint64(payload.UptimeSeconds),
		Heartbeats: &gateway.HeartbeatStats{
			Sent:   uint64(payload.Heartbeats.Sent),
			Failed: uint64(payload.Heartbeats.Failed),
		},
		Tasks: &gateway.TaskStats{
			Fetched:  uint64(payload.Tasks.Fetched),
			Executed: uint64(payload.Tasks.Executed),
			Failed:   uint64(payload.Tasks.Failed),
		},
		Queue: &gateway.QueueStats{
			Depth:    uint64(payload.Queue.Depth),
			Capacity: uint64(payload.Queue.Capacity),
		},
		Workers: &gateway.WorkerStats{
			Active: uint64(payload.Workers.Active),
		},
	}
	if !payload.CapturedAt.IsZero() {
		metrics.CapturedAt = timestamppb.New(payload.CapturedAt)
	}
	if payload.Heartbeats.LastSuccess != nil && !payload.Heartbeats.LastSuccess.IsZero() {
		metrics.Heartbeats.LastSuccess = timestamppb.New(*payload.Heartbeats.LastSuccess)
	}
	msg := &gateway.ProbeMessage{
		Body: &gateway.ProbeMessage_Metrics{Metrics: metrics},
	}
	return t.send(msg)
}

func (t *GRPCTransport) send(msg *gateway.ProbeMessage) error {
	t.sendMu.Lock()
	defer t.sendMu.Unlock()

	if t.baseCtx.Err() != nil {
		return t.baseCtx.Err()
	}
	if t.stream == nil {
		return errors.New("grpc stream is not connected")
	}
	if err := t.stream.Send(msg); err != nil {
		t.logger.Warn().
			Err(err).
			Str("message_type", messageType(msg)).
			Str("connection_state", t.connectionState()).
			Msg("grpc stream send failed")
		return err
	}
	return nil
}

func (t *GRPCTransport) Close() error {
	if t.baseCancel != nil {
		t.baseCancel()
	}

	t.sendMu.Lock()
	stream := t.stream
	streamCancel := t.cancelFunc
	t.stream = nil
	t.cancelFunc = nil
	t.sendMu.Unlock()

	if streamCancel != nil {
		streamCancel()
	}
	if stream != nil {
		_ = stream.CloseSend()
	}
	if t.conn != nil {
		return t.conn.Close()
	}
	return nil
}

func (t *GRPCTransport) Commands() <-chan Command {
	return t.commands
}

func (t *GRPCTransport) Tasks() <-chan api.Task {
	return t.tasks
}

func (t *GRPCTransport) AcknowledgeTask(ctx context.Context, taskID string) error {
	if taskID == "" {
		return nil
	}
	return t.send(&gateway.ProbeMessage{
		Body: &gateway.ProbeMessage_TaskAck{
			TaskAck: &gateway.TaskAck{
				TaskId:     taskID,
				ReceivedAt: timestamppb.Now(),
			},
		},
	})
}

func (t *GRPCTransport) handleConfigUpdate(update *gateway.ConfigUpdate) {
	appliedIDs := make([]string, 0, len(update.GetSchedules()))
	for _, cfg := range update.GetSchedules() {
		appliedIDs = append(appliedIDs, cfg.GetScheduleId())
	}
	command := Command{
		Name:         "config.update",
		ConfigUpdate: update,
	}
	select {
	case t.commands <- command:
	default:
		t.logger.Warn().Msg("command buffer full, dropping config update")
	}
	go t.sendConfigAck(update.GetVersion(), appliedIDs)
}

func (t *GRPCTransport) sendConfigAck(version uint64, scheduleIDs []string) {
	msg := &gateway.ProbeMessage{
		Body: &gateway.ProbeMessage_ConfigAck{
			ConfigAck: &gateway.ConfigAck{
				Version:            version,
				AppliedScheduleIds: scheduleIDs,
			},
		},
	}
	if err := t.send(msg); err != nil {
		t.logger.Warn().Err(err).Uint64("version", version).Msg("failed to ack config update")
	}
}

func buildDialCredentials(cfg config.Config) (grpc.DialOption, error) {
	if cfg.GRPCInsecure {
		return grpc.WithTransportCredentials(insecure.NewCredentials()), nil
	}
	tlsConfig := &tls.Config{}
	if cfg.GRPCCAFile != "" {
		caBytes, err := os.ReadFile(cfg.GRPCCAFile)
		if err != nil {
			return nil, fmt.Errorf("read grpc_ca_file: %w", err)
		}
		pool := x509.NewCertPool()
		if !pool.AppendCertsFromPEM(caBytes) {
			return nil, fmt.Errorf("grpc_ca_file contains no certificates")
		}
		tlsConfig.RootCAs = pool
	}
	if cfg.GRPCClientCert != "" && cfg.GRPCClientKey != "" {
		certificate, err := tls.LoadX509KeyPair(cfg.GRPCClientCert, cfg.GRPCClientKey)
		if err != nil {
			return nil, fmt.Errorf("load client TLS cert/key: %w", err)
		}
		tlsConfig.Certificates = []tls.Certificate{certificate}
	}
	return grpc.WithTransportCredentials(credentials.NewTLS(tlsConfig)), nil
}

func (t *GRPCTransport) reconnectStream() error {
	backoffDelay := time.Second

	for {
		if t.baseCtx.Err() != nil {
			return t.baseCtx.Err()
		}

		streamCtx, streamCancel := context.WithCancel(t.baseCtx)
		stream, err := t.client.Connect(streamCtx)
		if err == nil {
			t.sendMu.Lock()
			oldStream := t.stream
			oldCancel := t.cancelFunc
			t.stream = stream
			t.cancelFunc = streamCancel
			t.sendMu.Unlock()

			if oldCancel != nil {
				oldCancel()
			}
			if oldStream != nil {
				_ = oldStream.CloseSend()
			}

			if err := t.sendHello(); err != nil {
				t.logger.Warn().Err(err).Msg("grpc stream hello failed after reconnect")
				streamCancel()
				_ = stream.CloseSend()
			} else {
				t.logger.Info().
					Str("connection_state", t.connectionState()).
					Msg("grpc stream connected")
				return nil
			}
		} else {
			streamCancel()
			t.logger.Warn().Err(err).Msg("grpc stream reconnect attempt failed")
		}

		select {
		case <-t.baseCtx.Done():
			return t.baseCtx.Err()
		case <-time.After(backoffDelay):
		}

		if backoffDelay < 10*time.Second {
			backoffDelay *= 2
			if backoffDelay > 10*time.Second {
				backoffDelay = 10 * time.Second
			}
		}
	}
}

func (t *GRPCTransport) currentStream() gateway.ProbeGateway_ConnectClient {
	t.sendMu.Lock()
	defer t.sendMu.Unlock()
	return t.stream
}

func (t *GRPCTransport) connectionState() string {
	if t == nil || t.conn == nil {
		return connectivity.Idle.String()
	}
	return t.conn.GetState().String()
}

func messageType(msg *gateway.ProbeMessage) string {
	if msg == nil || msg.Body == nil {
		return "<nil>"
	}
	return fmt.Sprintf("%T", msg.Body)
}
