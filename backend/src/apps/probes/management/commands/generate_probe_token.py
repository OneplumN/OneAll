from __future__ import annotations

import secrets
import uuid

from django.core.management.base import BaseCommand, CommandError

from apps.probes.models import ProbeNode


class Command(BaseCommand):
    help = "Generate or rotate probe API tokens"

    def add_arguments(self, parser):
        parser.add_argument("node_id", help="Probe node ID or name")
        parser.add_argument(
            "--token",
            help="Provide custom token (min 16 chars). If omitted a random token will be generated.",
        )
        parser.add_argument(
            "--length",
            type=int,
            default=32,
            help="Random token length when --token omitted (default: 32)",
        )

    def handle(self, *args, **options):
        node_identifier = options["node_id"]
        token = options.get("token")
        length = options["length"]

        probe = self._resolve_probe(node_identifier)

        if token:
            if len(token) < 16:
                raise CommandError("Provided token must be at least 16 characters long")
        else:
            if length < 16:
                raise CommandError("Random token length must be >= 16")
            token = secrets.token_urlsafe(length)[:length]

        probe.set_api_token(token)
        probe.touch_authenticated()

        self.stdout.write(self.style.SUCCESS("Probe token updated"))
        self.stdout.write(f"Probe: {probe.name} ({probe.id})")
        self.stdout.write(f"Token hint: {probe.api_token_hint}")
        self.stdout.write(self.style.WARNING("Store this token immediately; it will not be shown again."))
        self.stdout.write(token)

    def _resolve_probe(self, identifier: str) -> ProbeNode:
        uuid_obj = None
        try:
            uuid_obj = uuid.UUID(str(identifier))
        except (ValueError, AttributeError):
            pass
        if uuid_obj is not None:
            try:
                return ProbeNode.objects.get(id=str(uuid_obj))
            except ProbeNode.DoesNotExist:
                pass
        try:
            return ProbeNode.objects.get(name=identifier)
        except ProbeNode.DoesNotExist as exc:
            raise CommandError(f"Probe node '{identifier}' not found") from exc
