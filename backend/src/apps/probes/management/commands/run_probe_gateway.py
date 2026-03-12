from __future__ import annotations

from django.core.management.base import BaseCommand

from apps.probes.streaming.server import run_server


class Command(BaseCommand):
    help = "Run the probe gRPC gateway server."

    def add_arguments(self, parser):
        parser.add_argument("--host", type=str, default="0.0.0.0", help="Bind host for the gRPC gateway")
        parser.add_argument("--port", type=int, default=50051, help="Bind port for the gRPC gateway")
        parser.add_argument(
            "--max-concurrent",
            type=int,
            default=500,
            help="Maximum concurrent RPCs handled by the gateway",
        )
        parser.add_argument("--cert-file", type=str, default=None, help="TLS certificate for gRPC gateway")
        parser.add_argument("--key-file", type=str, default=None, help="TLS private key for gRPC gateway")
        parser.add_argument(
            "--client-ca",
            type=str,
            default=None,
            help="CA certificate to require client TLS authentication",
        )

    def handle(self, *args, **options):
        run_server(
            host=options["host"],
            port=options["port"],
            max_concurrent_rpcs=options["max_concurrent"],
            cert_file=options["cert_file"],
            key_file=options["key_file"],
            client_ca_file=options["client_ca"],
        )
