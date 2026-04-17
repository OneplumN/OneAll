from __future__ import annotations

import asyncio
import logging
from pathlib import Path

import grpc

from probes.v1 import gateway_pb2_grpc
from apps.probes.streaming.service import ProbeGatewayService

logger = logging.getLogger(__name__)


async def serve(
    *,
    host: str = "0.0.0.0",
    port: int = 50051,
    max_concurrent_rpcs: int = 500,
    cert_file: str | None = None,
    key_file: str | None = None,
    client_ca_file: str | None = None,
) -> None:
    server = grpc.aio.server(
        options=[
            # Application heartbeats arrive every 30s, so the gateway does not need
            # aggressive transport-level keepalive pings. Keep this very conservative
            # to avoid server-initiated ping storms on fresh connections.
            ("grpc.keepalive_time_ms", 600_000),
            ("grpc.keepalive_timeout_ms", 20_000),
            ("grpc.keepalive_permit_without_calls", 1),
            # Disable bandwidth-delay probe pings; they were observed to fire
            # immediately after stream establishment and correlate with client resets.
            ("grpc.http2.bdp_probe", 0),
            # Allow client keepalive pings without data to prevent connection resets
            ("grpc.http2.max_pings_without_data", 0),
            ("grpc.http2.min_ping_interval_without_data_ms", 10_000),
            # Disable ping strike enforcement; application heartbeats already provide
            # active liveness and some client/server combinations proved overly strict.
            ("grpc.http2.max_ping_strikes", 0),
        ],
        maximum_concurrent_rpcs=max_concurrent_rpcs,
    )
    service = ProbeGatewayService()
    gateway_pb2_grpc.add_ProbeGatewayServicer_to_server(service, server)
    bind_address = f"{host}:{port}"
    credentials = _build_server_credentials(cert_file, key_file, client_ca_file)
    if credentials:
        server.add_secure_port(bind_address, credentials)
    else:
        server.add_insecure_port(bind_address)
    logger.info("Probe gateway listening on %s", bind_address)
    await server.start()
    await server.wait_for_termination()


def run_server(**kwargs) -> None:
    asyncio.run(serve(**kwargs))


def _build_server_credentials(
    cert_file: str | None,
    key_file: str | None,
    client_ca_file: str | None,
) -> grpc.ServerCredentials | None:
    if not cert_file or not key_file:
        return None
    cert_path = Path(cert_file)
    key_path = Path(key_file)
    if not cert_path.exists() or not key_path.exists():
        raise FileNotFoundError("server certificate or key file not found")
    certificate_chain = cert_path.read_bytes()
    private_key = key_path.read_bytes()
    key_cert_pair = ((private_key, certificate_chain),)
    if client_ca_file:
        ca_path = Path(client_ca_file)
        if not ca_path.exists():
            raise FileNotFoundError("client CA file not found")
        return grpc.ssl_server_credentials(
            key_cert_pair,
            root_certificates=ca_path.read_bytes(),
            require_client_auth=True,
        )
    return grpc.ssl_server_credentials(key_cert_pair)
