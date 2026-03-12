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
	"google.golang.org/grpc/credentials"
	"google.golang.org/grpc/credentials/insecure"
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
	conn       *grpc.ClientConn
	client     gateway.ProbeGatewayClient
	stream     gateway.ProbeGateway_ConnectClient
	sendMu     sync.Mutex
	tasks      chan api.Task
	errMu      sync.RWMutex
	recvErr    error
	cancelFunc context.CancelFunc
	commands   chan Command
}

// NewGRPCTransport establishes a streaming connection to the controller.
func NewGRPCTransport(ctx context.Context, cfg config.Config, protocols []string, logger zerolog.Logger) (*GRPCTransport, error) {
	if cfg.GRPCGateway == "" {
		return nil, errors.New("grpc gateway address required")
	}
	dialCtx, cancel := context.WithTimeout(ctx, 10*time.Second)
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
	)
	if err != nil {
		return nil, err
	}

	client := gateway.NewProbeGatewayClient(conn)
	streamCtx, streamCancel := context.WithCancel(ctx)
	stream, err := client.Connect(streamCtx)
	if err != nil {
		streamCancel()
		_ = conn.Close()
		return nil, err
	}

	t := &GRPCTransport{
		cfg:        cfg,
		logger:     logger,
		protocols:  protocols,
		conn:       conn,
		client:     client,
		stream:     stream,
		tasks:      make(chan api.Task, 128),
		commands:   make(chan Command, 16),
		cancelFunc: streamCancel,
	}
	if err := t.sendHello(); err != nil {
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
		response, err := t.stream.Recv()
		if err != nil {
			t.setError(err)
			close(t.tasks)
			return
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

func (t *GRPCTransport) setError(err error) {
	t.errMu.Lock()
	defer t.errMu.Unlock()
	if t.recvErr == nil {
		t.recvErr = err
	}
}

func (t *GRPCTransport) getError() error {
	t.errMu.RLock()
	defer t.errMu.RUnlock()
	return t.recvErr
}

func (t *GRPCTransport) SendHeartbeat(ctx context.Context, payload api.HeartbeatRequest) error {
	heartbeat := &gateway.Heartbeat{
		SentAt:        timestamppb.New(payload.SentAt),
		Status:        payload.Status,
		CpuUsage:      payload.Metrics["cpu_usage"],
		MemoryUsageMb: payload.Metrics["memory_usage_mb"],
		QueueDepth:    uint32(payload.Metrics["queue_depth"]),
		ActiveTasks:   uint32(payload.Metrics["active_tasks"]),
		IpAddress:     payload.IPAddress,
	}
	return t.send(&gateway.ProbeMessage{
		Body: &gateway.ProbeMessage_Heartbeat{Heartbeat: heartbeat},
	})
}

func (t *GRPCTransport) FetchTasks(ctx context.Context, limit int) ([]api.Task, error) {
	if err := t.getError(); err != nil {
		return nil, err
	}
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
				if err := t.getError(); err != nil {
					return collected, err
				}
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
	return t.send(&gateway.ProbeMessage{
		Body: &gateway.ProbeMessage_Result{Result: payload},
	})
}

func (t *GRPCTransport) PublishMetrics(ctx context.Context, payload api.MetricsPayload) error {
	if err := t.getError(); err != nil {
		return err
	}
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
	if err := t.getError(); err != nil {
		return err
	}
	t.sendMu.Lock()
	defer t.sendMu.Unlock()
	return t.stream.Send(msg)
}

func (t *GRPCTransport) Close() error {
	if t.cancelFunc != nil {
		t.cancelFunc()
	}
	if t.stream != nil {
		_ = t.stream.CloseSend()
	}
	if t.conn != nil {
		return t.conn.Close()
	}
	return nil
}

func (t *GRPCTransport) Commands() <-chan Command {
	return t.commands
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
