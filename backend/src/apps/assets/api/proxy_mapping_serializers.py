from __future__ import annotations

from rest_framework import serializers

from apps.assets.models import ProxyMapping


class ProxyMappingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProxyMapping
        fields = ("id", "proxy", "display_name", "remark", "is_active", "updated_at")


class ProxyMappingUpsertItemSerializer(serializers.Serializer):
    proxy = serializers.CharField(max_length=128)
    display_name = serializers.CharField(max_length=256, allow_blank=True, required=False)
    remark = serializers.CharField(max_length=256, allow_blank=True, required=False)
    is_active = serializers.BooleanField(required=False)


class ProxyMappingUpsertSerializer(serializers.Serializer):
    items = ProxyMappingUpsertItemSerializer(many=True)

