from __future__ import annotations

import asyncio
import logging
import uuid
from typing import AsyncIterator

import grpc
from django.db import close_old_connections
from django.utils import timezone
from google.protobuf import json_format

from apps.probes.models import ProbeNode, ProbeSchedule, ProbeScheduleExecution
from apps.probes.services import (
    probe_metrics_service,
    probe_monitor_service,
    schedule_config_service,
    schedule_execution_service,
)
from probes.v1 import gateway_pb2, gateway_pb2_grpc

logger = logging.getLogger(__name__)

DEFAULT_HEARTBEAT_INTERVAL = 30
DEFAULT_MAX_CONCURRENCY = 4


class GatewayError(Exception):
    def __init__(self, code: grpc.StatusCode, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class ProbeGatewayService(gateway_pb2_grpc.ProbeGatewayServicer):
    """gRPC service responsible for bidirectional communication with probes."""

    async def Connect(
        self,
        request_iterator: AsyncIterator[gateway_pb2.ProbeMessage],
        context: grpc.aio.ServicerContext,
    ) -> AsyncIterator[gateway_pb2.ServerMessage]:
        close_old_connections()
        probe: ProbeNode | None = None
        probe_id: str | None = None
        send_queue: asyncio.Queue[gateway_pb2.ServerMessage] = asyncio.Queue()
        send_task = asyncio.create_task(send_queue.get())
        recv_task = asyncio.create_task(request_iterator.__anext__())

        try:
            while True:
                done, _ = await asyncio.wait({send_task, recv_task}, return_when=asyncio.FIRST_COMPLETED)

                if send_task in done:
                    try:
                        payload = send_task.result()
                    except asyncio.CancelledError:
                        break
                    yield payload
                    send_task = asyncio.create_task(send_queue.get())

                if recv_task in done:
                    try:
                        message = recv_task.result()
                    except StopAsyncIteration:
                        break
                    except asyncio.CancelledError:
                        break
                    finally:
                        recv_task = asyncio.create_task(request_iterator.__anext__())

                    close_old_connections()
                    body = message.WhichOneof("body")
                    if body == "hello":
                        try:
                            probe = await asyncio.get_event_loop().run_in_executor(
                                None, self._authenticate_probe, message.hello
                            )
                        except GatewayError as exc:
                            await context.abort(exc.code, exc.message)
                        probe_id = str(probe.id)
                        await send_queue.put(gateway_pb2.ServerMessage(ack=self._build_ack(probe)))
                        await send_queue.put(self._build_config_refresh_command())
                        config_update_message = await self._build_config_update_message(probe)
                        await send_queue.put(config_update_message)
                        continue

                    if probe is None or probe_id is None:
                        await context.abort(grpc.StatusCode.UNAUTHENTICATED, "probe must authenticate first")
                        break

                    if body == "heartbeat":
                        await asyncio.get_event_loop().run_in_executor(
                            None, self._handle_heartbeat, probe, message.heartbeat
                        )
                        await self._flush_pending_refresh_requests(probe, send_queue)
                    elif body == "result":
                        await asyncio.get_event_loop().run_in_executor(
                            None, self._handle_schedule_result, probe, message.result
                        )
                        await self._flush_pending_refresh_requests(probe, send_queue)
                    elif body == "metrics":
                        await asyncio.get_event_loop().run_in_executor(
                            None, self._handle_runtime_metrics, probe, message.metrics
                        )
                        await self._flush_pending_refresh_requests(probe, send_queue)
                    elif body == "config_ack":
                        self._handle_config_ack(probe, message.config_ack)
                        await self._flush_pending_refresh_requests(probe, send_queue)
                    elif body == "task_request":
                        logger.debug("Probe %s sent legacy task_request; tasks are config-driven now", probe.id)
                    else:
                        logger.warning("Probe %s sent unsupported payload %s", probe.id, body)
        finally:
            send_task.cancel()
            recv_task.cancel()

    def _authenticate_probe(self, hello: gateway_pb2.ProbeHello) -> ProbeNode:
        try:
            probe_uuid = uuid.UUID(hello.probe_id)
        except (ValueError, TypeError):
            raise GatewayError(grpc.StatusCode.INVALID_ARGUMENT, "invalid probe id")

        try:
            probe = ProbeNode.objects.get(id=probe_uuid)
        except ProbeNode.DoesNotExist:
            raise GatewayError(grpc.StatusCode.NOT_FOUND, "probe not registered")

        if not probe.check_api_token(hello.token):
            raise GatewayError(grpc.StatusCode.UNAUTHENTICATED, "invalid token")

        updates: dict[str, object] = {
            "supported_protocols": list(hello.supported_protocols),
            "status": "online",
            "last_authenticated_at": timezone.now(),
        }
        ProbeNode.objects.filter(id=probe.id).update(**updates)
        probe.refresh_from_db(fields=["supported_protocols", "status", "last_authenticated_at"])
        return probe

    def _build_ack(self, probe: ProbeNode) -> gateway_pb2.HelloAck:
        config = probe.agent_config or {}
        heartbeat_interval = int(config.get("heartbeat_interval") or DEFAULT_HEARTBEAT_INTERVAL)
        max_concurrency = int(config.get("max_concurrent_tasks") or DEFAULT_MAX_CONCURRENCY)
        return gateway_pb2.HelloAck(
            probe_id=str(probe.id),
            heartbeat_interval_seconds=heartbeat_interval,
            max_concurrency=max_concurrency,
            message="probe authenticated",
        )

    def _handle_heartbeat(self, probe: ProbeNode, hb: gateway_pb2.Heartbeat) -> None:
        payload = {
            "status": hb.status or "online",
            "metrics": {
                "cpu_usage": hb.cpu_usage,
                "memory_usage_mb": hb.memory_usage_mb,
                "task_queue_depth": hb.queue_depth,
                "active_tasks": hb.active_tasks,
                "ip_address": hb.ip_address,
            },
        }
        probe_monitor_service.handle_heartbeat(probe=probe, payload=payload)

    def _handle_runtime_metrics(self, probe: ProbeNode, metrics: gateway_pb2.RuntimeMetrics) -> None:
        captured_at = metrics.captured_at.ToDatetime().replace(tzinfo=timezone.utc) if metrics.captured_at else timezone.now()
        payload = {
            "captured_at": captured_at,
            "uptime_seconds": metrics.uptime_seconds,
            "heartbeats": {
                "sent": metrics.heartbeats.sent if metrics.heartbeats else 0,
                "failed": metrics.heartbeats.failed if metrics.heartbeats else 0,
                "last_success": (
                    metrics.heartbeats.last_success.ToDatetime().replace(tzinfo=timezone.utc)
                    if metrics.heartbeats and metrics.heartbeats.last_success
                    else None
                ),
            },
            "tasks": {
                "fetched": metrics.tasks.fetched if metrics.tasks else 0,
                "executed": metrics.tasks.executed if metrics.tasks else 0,
                "failed": metrics.tasks.failed if metrics.tasks else 0,
            },
            "queue": {
                "depth": metrics.queue.depth if metrics.queue else 0,
                "capacity": metrics.queue.capacity if metrics.queue else 0,
            },
            "workers": {
                "active": metrics.workers.active if metrics.workers else 0,
            },
        }
        probe_metrics_service.record_runtime_snapshot(probe=probe, payload=payload)

    def _build_config_refresh_command(self) -> gateway_pb2.ServerMessage:
        return gateway_pb2.ServerMessage(command=gateway_pb2.ControlCommand(command="config.refresh"))

    async def _build_config_update_message(self, probe: ProbeNode) -> gateway_pb2.ServerMessage:
        loop = asyncio.get_running_loop()
        update = await loop.run_in_executor(None, schedule_config_service.build_config_update_for_probe, probe)
        return gateway_pb2.ServerMessage(config_update=update)

    async def _flush_pending_refresh_requests(
        self,
        probe: ProbeNode,
        send_queue: asyncio.Queue,
    ) -> None:
        loop = asyncio.get_running_loop()
        has_pending = await loop.run_in_executor(None, schedule_config_service.pop_pending_refresh_requests, probe)
        if not has_pending:
            return
        await send_queue.put(self._build_config_refresh_command())
        update_message = await self._build_config_update_message(probe)
        await send_queue.put(update_message)

    def _handle_config_ack(self, probe: ProbeNode, ack: gateway_pb2.ConfigAck) -> None:
        logger.info(
            "Probe %s acknowledged config version %s (%s schedule(s))",
            probe.id,
            ack.version,
            len(ack.applied_schedule_ids),
        )

    def _handle_schedule_result(self, probe: ProbeNode, result: gateway_pb2.TaskResult) -> None:
        schedule_id = result.schedule_id
        if not schedule_id:
            logger.warning("Probe %s sent result without schedule_id", probe.id)
            return
        try:
            schedule = ProbeSchedule.objects.get(id=schedule_id)
        except ProbeSchedule.DoesNotExist:
            logger.warning("Schedule %s not found for probe %s", schedule_id, probe.id)
            return
        if result.scheduled_at:
            scheduled_at = result.scheduled_at.ToDatetime().replace(tzinfo=timezone.utc)
        elif result.finished_at:
            scheduled_at = result.finished_at.ToDatetime().replace(tzinfo=timezone.utc)
        else:
            scheduled_at = timezone.now()
        metadata = json_format.MessageToDict(result.metadata, preserving_proto_field_name=True) if result.metadata else {}
        status = ProbeScheduleExecution.normalize_status(result.status or "failed")
        schedule_execution_service.record_result(
            schedule=schedule,
            probe=probe,
            scheduled_at=scheduled_at,
            status=status,
            response_time_ms=int(result.response_time_ms),
            status_code=str(result.status_code),
            message=result.message,
            metadata=metadata or None,
        )
