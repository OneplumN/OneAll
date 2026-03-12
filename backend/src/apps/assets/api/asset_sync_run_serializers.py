from __future__ import annotations

from rest_framework import serializers

from apps.assets.models import AssetSyncChange, AssetSyncRun


class AssetSyncRunSerializer(serializers.ModelSerializer):
    run_id = serializers.UUIDField(source="id", read_only=True)

    class Meta:
        model = AssetSyncRun
        fields = [
            "run_id",
            "mode",
            "status",
            "source_filters",
            "started_at",
            "finished_at",
            "summary",
            "error_message",
            "created_at",
        ]


class AssetSyncChangeSerializer(serializers.ModelSerializer):
    change_id = serializers.UUIDField(source="id", read_only=True)
    record_id = serializers.UUIDField(source="record.id", read_only=True, allow_null=True)

    class Meta:
        model = AssetSyncChange
        fields = [
            "change_id",
            "record_id",
            "source",
            "external_id",
            "action",
            "changed_fields",
            "before",
            "after",
            "created_at",
        ]

