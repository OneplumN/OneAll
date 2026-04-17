from __future__ import annotations

from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from apps.assets.models import AssetRecord


class AssetRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssetRecord
        fields = [
            "created_at",
            "updated_at",
            "id",
            "source",
            "external_id",
            "name",
            "system_name",
            "owners",
            "contacts",
            "metadata",
            "synced_at",
            "sync_status",
            "is_removed",
            "removed_at",
            "last_seen_at",
        ]
        read_only_fields = fields


class AssetRecordCreateSerializer(serializers.ModelSerializer):
    external_id = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = AssetRecord
        fields = [
            "source",
            "external_id",
            "name",
            "system_name",
            "owners",
            "contacts",
            "metadata",
            "sync_status",
        ]
        extra_kwargs = {
            "source": {"required": False},
            "external_id": {"required": False},
            "name": {"required": True},
            "metadata": {"required": False},
            "sync_status": {"required": False},
        }
        validators = [
            UniqueTogetherValidator(
                queryset=AssetRecord.objects.all(),
                fields=["source", "external_id"],
                message="创建失败：该资产已存在，请勿重复创建。可在资产列表中搜索并编辑已有资产。",
            )
        ]

    def to_internal_value(self, data):
        if isinstance(data, dict):
            ext = data.get('external_id')
            name = data.get('name')
            if (ext is None or ext == '') and name:
                data = dict(data)
                data['external_id'] = name
        return super().to_internal_value(data)

    def validate(self, attrs):
        attrs.setdefault("source", AssetRecord.Source.MANUAL)
        attrs.setdefault("external_id", attrs.get("name"))
        attrs.setdefault("owners", [])
        attrs.setdefault("contacts", [])
        attrs.setdefault("metadata", {})
        return attrs

    def create(self, validated_data):
        if not validated_data.get("sync_status"):
            validated_data["sync_status"] = "manual"
        return super().create(validated_data)


class AssetRecordUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssetRecord
        fields = [
            "external_id",
            "name",
            "system_name",
            "owners",
            "contacts",
            "metadata",
        ]
        extra_kwargs = {
            "external_id": {"required": False},
            "name": {"required": False},
            "system_name": {"required": False},
            "owners": {"required": False},
            "contacts": {"required": False},
            "metadata": {"required": False},
        }

    def validate_metadata(self, value):
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise serializers.ValidationError("metadata 必须是对象")
        return value
