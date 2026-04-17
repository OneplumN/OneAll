from __future__ import annotations

from django.db import models

from apps.core.models.base import BaseModel


class AssetModel(BaseModel):
    """Configurable asset model definition bound to a sync script.

    This describes how a logical asset type looks inside OneAll (fields, unique key),
    and which sync script (identified by script_id) should be used to populate it.
    """

    key = models.CharField(max_length=64, unique=True)
    label = models.CharField(max_length=128)
    category = models.CharField(max_length=64, blank=True)

    # List of field definitions: [{"key": "...", "label": "...", "type": "...", ...}, ...]
    fields = models.JSONField(default=list)

    # Business unique key: list of field keys that must uniquely identify a record.
    unique_key = models.JSONField(default=list)

    # Identifier for the uploaded sync script; mapping to a concrete file path is handled by services.
    script_id = models.CharField(max_length=128, blank=True)

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "assets_asset_model"
        verbose_name = "Asset Model"
        verbose_name_plural = "Asset Models"

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"{self.key} ({self.label})"

