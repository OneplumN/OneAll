from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db.models import QuerySet

from apps.alerts.models import AlertCheck
from apps.alerts.services import apply_resolution_snapshot


class Command(BaseCommand):
    help = "Recompute target-resolution snapshot fields for existing alert checks."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--batch-size",
            type=int,
            default=200,
            help="Number of AlertCheck rows to process per batch.",
        )

    def handle(self, *args, **options):
        batch_size = max(1, int(options["batch_size"]))
        queryset: QuerySet[AlertCheck] = AlertCheck.objects.order_by("created_at", "id")

        processed = 0
        while True:
            batch = list(queryset[processed : processed + batch_size])
            if not batch:
                break

            for check in batch:
                apply_resolution_snapshot(check)
            processed += len(batch)

        self.stdout.write(
            self.style.SUCCESS(
                f"Backfilled resolution snapshots for {processed} checks."
            )
        )
