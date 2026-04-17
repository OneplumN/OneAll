from __future__ import annotations

import asyncio
from dataclasses import dataclass
import logging
import uuid
from typing import AsyncIterator, Callable

import grpc
from django.utils import timezone
from google.protobuf import json_format, struct_pb2

from apps.monitoring.models import DetectionTask
from apps.monitoring.services import detection_service
from apps.monitoring.tasks.execute_detection import expire_detection_task
from apps.probes.models import ProbeNode, ProbeSchedule, ProbeScheduleExecution
from apps.probes.services import (
    probe_metrics_service,
    probe_monitor_service,
    schedule_config_service,
    schedule_execution_service,
)
from apps.probes.services import probe_task_service
from probes.v1 import gateway_pb2, gateway_pb2_grpc

logger = logging.getLogger(__name__)

DEFAULT_HEARTBEAT_INTERVAL = 30
DEFAULT_MAX_CONCURRENCY = 4
DIRECT_TASK_POLL_INTERVAL_SECONDS = 1


class GatewayError(Exception):
    def __init__(self, code: grpc.StatusCode, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(slots=True)
class OutboundMessage:
    payload: gateway_pb2.ServerMessage
    on_sent: Callable[[], None] | None = None


class ProbeGatewayService(gateway_pb2_grpc.ProbeGatewayServicer):
    """gRPC service responsible for bidirectional communication with probes."""

    async def Connect(
        self,
        request_iterator: AsyncIterator[gateway_pb2.ProbeMessage],
        context: grpc.aio.ServicerContext,
    ) -> AsyncIterator[gateway_pb2.ServerMessage]:
        peer = context.peer()
        send_queue: asyncio.Queue[OutboundMessage | object] = asyncio.Queue()
        stop_event = asyncio.Event()
        stream_closed = object()
        state: dict[str, ProbeNode | str | None] = {
            "probe": None,
            "probe_id": None,
            "stream_id": str(uuid.uuid4()),
            "last_message_type": None,
        }
        loop = asyncio.get_running_loop()
        logger.info("Probe stream opened", extra=self._log_extra(state=state, peer=peer))

        recv_task = asyncio.create_task(
            self._consume_probe_messages(
                request_iterator=request_iterator,
                context=context,
                send_queue=send_queue,
                stop_event=stop_event,
                peer=peer,
                state=state,
                stream_closed=stream_closed,
            )
        )
        tick_task = asyncio.create_task(
            self._periodic_flush(
                send_queue=send_queue,
                stop_event=stop_event,
                peer=peer,
                state=state,
            )
        )

        try:
            while True:
                outbound = await send_queue.get()
                if outbound is stream_closed:
                    break
                message_type = outbound.payload.WhichOneof("body")
                try:
                    yield outbound.payload
                    if outbound.on_sent is not None:
                        await loop.run_in_executor(None, outbound.on_sent)
                except asyncio.CancelledError:
                    logger.info(
                        "Probe stream send cancelled",
                        extra=self._log_extra(
                            state=state,
                            peer=peer,
                            message_type=message_type,
                        ),
                    )
                    raise
                except BaseException:  # pragma: no cover - defensive logging
                    logger.exception(
                        "Probe stream send failed",
                        extra=self._log_extra(
                            state=state,
                            peer=peer,
                            message_type=message_type,
                        ),
                    )
                    raise

                recv_exc = self._background_task_error(recv_task)
                if recv_exc is not None:
                    raise recv_exc
                tick_exc = self._background_task_error(tick_task)
                if tick_exc is not None:
                    raise tick_exc

            recv_exc = self._background_task_error(recv_task)
            if recv_exc is not None:
                raise recv_exc
            tick_exc = self._background_task_error(tick_task)
            if tick_exc is not None:
                raise tick_exc
        except asyncio.CancelledError:
            logger.info(
                "Probe stream cancelled",
                extra=self._log_extra(state=state, peer=peer),
            )
            raise
        except BaseException:  # pragma: no cover - defensive logging
            logger.exception("Probe stream crashed", extra=self._log_extra(state=state, peer=peer))
            raise
        finally:
            stop_event.set()
            recv_task.cancel()
            tick_task.cancel()
            await asyncio.gather(recv_task, tick_task, return_exceptions=True)
            logger.info("Probe stream closed", extra=self._log_extra(state=state, peer=peer))

    async def _consume_probe_messages(
        self,
        request_iterator: AsyncIterator[gateway_pb2.ProbeMessage],
        context: grpc.aio.ServicerContext,
        send_queue: asyncio.Queue[OutboundMessage | object],
        stop_event: asyncio.Event,
        peer: str,
        state: dict[str, ProbeNode | str | None],
        stream_closed: object,
    ) -> None:
        loop = asyncio.get_running_loop()

        try:
            async for message in request_iterator:
                body = message.WhichOneof("body")
                state["last_message_type"] = body
                if body == "hello":
                    try:
                        probe = await loop.run_in_executor(None, self._authenticate_probe, message.hello)
                    except GatewayError as exc:
                        await context.abort(exc.code, exc.message)
                    probe_id = str(probe.id)
                    state["probe"] = probe
                    state["probe_id"] = probe_id
                    logger.info("Probe stream authenticated", extra=self._log_extra(state=state, peer=peer))
                    try:
                        await send_queue.put(OutboundMessage(payload=gateway_pb2.ServerMessage(ack=self._build_ack(probe))))
                        await self._flush_pending_detection_tasks(probe, send_queue)
                    except Exception:  # pragma: no cover - defensive logging
                        logger.exception(
                            "Unhandled error while bootstrapping probe stream",
                            extra=self._log_extra(state=state, peer=peer, body=body),
                        )
                    continue

                probe = state["probe"]
                probe_id = state["probe_id"]
                if probe is None or probe_id is None:
                    await context.abort(grpc.StatusCode.UNAUTHENTICATED, "probe must authenticate first")
                    break

                try:
                    if body == "heartbeat":
                        await loop.run_in_executor(None, self._handle_heartbeat, probe, message.heartbeat)
                        await self._flush_pending_refresh_requests(probe, send_queue)
                    elif body == "result":
                        await loop.run_in_executor(None, self._handle_schedule_result, probe, message.result)
                        await self._flush_pending_refresh_requests(probe, send_queue)
                    elif body == "metrics":
                        await loop.run_in_executor(None, self._handle_runtime_metrics, probe, message.metrics)
                        await self._flush_pending_refresh_requests(probe, send_queue)
                    elif body == "config_ack":
                        self._handle_config_ack(probe, message.config_ack)
                        await self._flush_pending_refresh_requests(probe, send_queue)
                    elif body == "task_ack":
                        await loop.run_in_executor(None, self._handle_task_ack, probe, message.task_ack)
                    elif body == "task_request":
                        logger.debug("Probe %s sent legacy task_request; tasks are config-driven now", probe.id)
                    else:
                        logger.warning("Probe %s sent unsupported payload %s", probe.id, body)
                except Exception:  # pragma: no cover - defensive logging
                    logger.exception(
                        "Unhandled error while processing probe message",
                        extra=self._log_extra(state=state, peer=peer, body=body),
                    )
        except asyncio.CancelledError:
            logger.info("Probe stream receive task cancelled", extra=self._log_extra(state=state, peer=peer))
            raise
        except Exception:
            logger.exception("Probe stream receive failed", extra=self._log_extra(state=state, peer=peer))
            raise
        finally:
            if not stop_event.is_set():
                stop_event.set()
                await send_queue.put(stream_closed)
        logger.info("Probe stream closed by client", extra=self._log_extra(state=state, peer=peer))

    async def _periodic_flush(
        self,
        send_queue: asyncio.Queue[OutboundMessage | object],
        stop_event: asyncio.Event,
        peer: str,
        state: dict[str, ProbeNode | str | None],
    ) -> None:
        while not stop_event.is_set():
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=DIRECT_TASK_POLL_INTERVAL_SECONDS)
                break
            except TimeoutError:
                pass

            probe = state["probe"]
            probe_id = state["probe_id"]
            if probe is None or probe_id is None:
                continue
            try:
                await self._flush_pending_refresh_requests(probe, send_queue)
                await self._flush_pending_detection_tasks(probe, send_queue)
            except asyncio.CancelledError:
                logger.info("Probe stream tick task cancelled", extra=self._log_extra(state=state, peer=peer))
                raise
            except Exception:  # pragma: no cover - defensive logging
                logger.exception(
                    "Unhandled error while flushing periodic probe updates",
                    extra=self._log_extra(state=state, peer=peer),
                )

    def _background_task_error(self, task: asyncio.Task) -> BaseException | None:
        if not task.done():
            return None
        try:
            return task.exception()
        except asyncio.CancelledError:
            return None

    def _log_extra(self, *, state: dict[str, ProbeNode | str | None], peer: str, **extra: object) -> dict[str, object]:
        payload: dict[str, object] = {
            "probe_id": state["probe_id"],
            "peer": peer,
            "stream_id": state["stream_id"],
            "last_message_type": state["last_message_type"],
        }
        payload.update(extra)
        return payload

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
        await send_queue.put(OutboundMessage(payload=self._build_config_refresh_command()))
        update_message = await self._build_config_update_message(probe)
        await send_queue.put(OutboundMessage(payload=update_message))

    async def _flush_pending_detection_tasks(
        self,
        probe: ProbeNode,
        send_queue: asyncio.Queue[OutboundMessage | object],
    ) -> None:
        loop = asyncio.get_running_loop()
        messages = await loop.run_in_executor(None, self._claim_pending_detection_tasks, probe)
        for message in messages:
            await send_queue.put(message)

    def _handle_config_ack(self, probe: ProbeNode, ack: gateway_pb2.ConfigAck) -> None:
        logger.info(
            "Probe %s acknowledged config version %s (%s schedule(s))",
            probe.id,
            ack.version,
            len(ack.applied_schedule_ids),
        )

    def _handle_task_ack(self, probe: ProbeNode, ack: gateway_pb2.TaskAck) -> None:
        try:
            detection_id = uuid.UUID(ack.task_id)
        except (TypeError, ValueError):
            logger.warning("Probe %s sent invalid task ack id %s", probe.id, ack.task_id)
            return

        updated = DetectionTask.objects.filter(
            id=detection_id,
            probe=probe,
            status=DetectionTask.Status.SCHEDULED,
            published_at__isnull=False,
        ).update(
            status=DetectionTask.Status.RUNNING,
            claimed_at=timezone.now(),
            updated_at=timezone.now(),
        )
        if updated:
            logger.info(
                "Probe task acknowledged",
                extra={
                    "probe_id": str(probe.id),
                    "task_id": ack.task_id,
                    "received_at": ack.received_at.ToDatetime().isoformat() if ack.received_at else None,
                },
            )

    def _handle_schedule_result(self, probe: ProbeNode, result: gateway_pb2.TaskResult) -> None:
        schedule_id = result.schedule_id
        metadata = json_format.MessageToDict(result.metadata, preserving_proto_field_name=True) if result.metadata else {}
        status = ProbeScheduleExecution.normalize_status(result.status or "failed")
        if not schedule_id:
            if result.task_id:
                self._handle_detection_result(probe, result, status, metadata or None)
            else:
                logger.warning("Probe %s sent result without schedule_id/task_id", probe.id)
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

    def _claim_pending_detection_tasks(self, probe: ProbeNode) -> list[OutboundMessage]:
        detection = (
            DetectionTask.objects.filter(
                probe=probe,
                status=DetectionTask.Status.SCHEDULED,
                metadata__execution_source="one_off",
            )
            .order_by("created_at", "id")
            .first()
        )
        if detection is None:
            return []

        metadata = self._build_detection_metadata(detection.metadata)
        timeout_seconds = probe_task_service.timeout_from_metadata(metadata)
        expected_status = probe_task_service.expect_status_from_metadata(metadata)
        struct_payload = struct_pb2.Struct()
        struct_payload.update(metadata)

        return [
            OutboundMessage(
                payload=gateway_pb2.ServerMessage(
                    task=gateway_pb2.TaskDispatch(
                        task_id=str(detection.id),
                        target=detection.target,
                        protocol=detection.protocol,
                        timeout_seconds=timeout_seconds,
                        expected_status_codes=[expected_status],
                        metadata=struct_payload,
                    )
                ),
                on_sent=lambda detection_id=detection.id, timeout_seconds=timeout_seconds: self._mark_detection_published(
                    detection_id=detection_id,
                    timeout_seconds=timeout_seconds,
                ),
            )
        ]

    def _mark_detection_published(self, *, detection_id: uuid.UUID, timeout_seconds: int) -> None:
        updated = DetectionTask.objects.filter(
            id=detection_id,
            status=DetectionTask.Status.SCHEDULED,
            published_at__isnull=True,
        ).update(
            published_at=timezone.now(),
            updated_at=timezone.now(),
        )
        if updated:
            self._schedule_detection_timeout(detection_id, timeout_seconds)

    def _schedule_detection_timeout(self, detection_id: uuid.UUID, timeout_seconds: int) -> None:
        try:
            expire_detection_task.apply_async(
                args=[str(detection_id)],
                countdown=max(timeout_seconds, 1),
            )
        except Exception:  # pragma: no cover - broker degradation should not block task dispatch
            logger.exception("Failed to enqueue detection timeout task", extra={"detection_id": str(detection_id)})

    def _build_detection_metadata(self, metadata: dict | None) -> dict:
        payload = dict(metadata or {})
        config = payload.get("config")
        if isinstance(config, dict):
            for key, value in config.items():
                payload.setdefault(key, value)
        return payload

    def _handle_detection_result(
        self,
        probe: ProbeNode,
        result: gateway_pb2.TaskResult,
        status: str,
        metadata: dict | None,
    ) -> None:
        try:
            detection = DetectionTask.objects.get(id=result.task_id)
        except (DetectionTask.DoesNotExist, ValueError):
            logger.warning("Detection task %s not found for probe %s", result.task_id, probe.id)
            return

        if detection.probe_id and detection.probe_id != probe.id:
            logger.warning("Detection task %s was reported by unexpected probe %s", detection.id, probe.id)
            return

        executed_at = (
            result.finished_at.ToDatetime().replace(tzinfo=timezone.utc)
            if result.finished_at
            else timezone.now()
        )
        status_code = str(result.status_code) if result.status_code else ""
        if status == ProbeScheduleExecution.Status.SUCCEEDED:
            detection_service.mark_detection_succeeded(
                detection.id,
                response_time_ms=int(result.response_time_ms),
                result_payload=metadata or {},
                status_code=status_code,
                message=result.message,
                executed_at=executed_at,
            )
            return

        if status == ProbeScheduleExecution.Status.MISSED:
            detection_service.mark_detection_timeout(detection.id)
            return

        detection_service.mark_detection_failed(
            detection.id,
            result.message or "检测失败",
            response_time_ms=int(result.response_time_ms) if result.response_time_ms else None,
            status_code=status_code,
            result_payload=metadata or {},
            executed_at=executed_at,
        )
