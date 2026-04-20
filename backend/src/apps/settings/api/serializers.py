from __future__ import annotations

from rest_framework import serializers

from apps.core.models.user import Role, User
from apps.core.outbound import UnsafeOutboundURLError, validate_outbound_hook_url
from apps.settings.models import AlertTemplate, PluginConfig, SystemSettings
from apps.settings.security import mask_sensitive_config, merge_sensitive_config
from apps.settings.services.alert_channel_service import CHANNEL_DEFINITIONS
from apps.settings.services.template_renderer import ALERT_VARIABLES, validate_alert_template
from apps.settings.utils import build_permission_catalog, get_all_permissions
from apps.core.permissions import PERMISSION_ALIASES
from apps.core.roles import get_primary_role


class NotificationChannelsSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False, allow_blank=True)
    webhook = serializers.URLField(required=False, allow_blank=True)


class LDAPIntegrationSerializer(serializers.Serializer):
    enabled = serializers.BooleanField(required=False)
    host = serializers.CharField(required=False, allow_blank=True)
    port = serializers.IntegerField(required=False, min_value=1, max_value=65535)
    use_ssl = serializers.BooleanField(required=False)
    base_dn = serializers.CharField(required=False, allow_blank=True)
    bind_dn = serializers.CharField(required=False, allow_blank=True)
    bind_password = serializers.CharField(required=False, allow_blank=True, write_only=True)
    has_bind_password = serializers.SerializerMethodField()
    user_filter = serializers.CharField(required=False, allow_blank=True)
    username_attr = serializers.CharField(required=False, allow_blank=True)
    display_name_attr = serializers.CharField(required=False, allow_blank=True)
    email_attr = serializers.CharField(required=False, allow_blank=True)
    sync_filter = serializers.CharField(required=False, allow_blank=True)
    sync_size_limit = serializers.IntegerField(required=False, min_value=1)
    default_role_ids = serializers.ListField(
        child=serializers.UUIDField(), required=False, allow_empty=True
    )

    def get_has_bind_password(self, obj):
        return bool(obj.get("bind_password"))


class IntegrationsSerializer(serializers.Serializer):
    ldap = LDAPIntegrationSerializer(required=False)
    # 资产中心相关配置，目前主要用于定义各资产类型的唯一键字段等，结构保持为开放 JSON：
    # {
    #   "types": {
    #     "cmdb-domain": { "unique_fields": ["domain"] },
    #     "zabbix-host": { "unique_fields": ["ip", "host_name"] },
    #     ...
    #   }
    # }
    assets = serializers.JSONField(required=False)


class SystemSettingsSerializer(serializers.ModelSerializer):
    notification_channels = NotificationChannelsSerializer()
    integrations = IntegrationsSerializer(required=False)

    class Meta:
        model = SystemSettings
        fields = [
            "id",
            "platform_name",
            "platform_logo",
            "default_timezone",
            "alert_escalation_threshold",
            "theme",
            "notification_channels",
            "integrations",
            "updated_at",
        ]
        read_only_fields = ["id", "updated_at"]

    def update(self, instance, validated_data):
        notification_channels = validated_data.pop("notification_channels", None)
        integrations = validated_data.pop("integrations", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if notification_channels is not None:
            instance.notification_channels = {
                **(instance.notification_channels or {}),
                **notification_channels,
            }

        if integrations is not None:
            current = dict(instance.integrations or {})
            for section, payload in integrations.items():
                current_section = dict(current.get(section) or {})
                for key, value in payload.items():
                    if key.startswith("has_"):
                        continue
                    if isinstance(value, str) and value == "":
                        current_section.pop(key, None)
                    else:
                        current_section[key] = value
                current[section] = current_section
            instance.integrations = current

        instance.save()
        return instance


class PluginConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = PluginConfig
        fields = [
            "id",
            "name",
            "type",
            "enabled",
            "config",
            "status",
            "last_checked_at",
            "last_message",
        ]
        read_only_fields = ["id", "status", "last_checked_at", "last_message"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["config"] = mask_sensitive_config(instance.config or {})
        return data

    def create(self, validated_data):
        config = validated_data.pop("config", {})
        merged_config = merge_sensitive_config({}, config)
        self._validate_plugin_config(merged_config)
        validated_data["config"] = merged_config
        return super().create(validated_data)

    def update(self, instance, validated_data):
        config = validated_data.pop("config", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if config is not None:
            merged_config = merge_sensitive_config(instance.config, config)
            self._validate_plugin_config(merged_config)
            instance.config = merged_config
        instance.save()
        return instance

    @staticmethod
    def _validate_plugin_config(config: dict) -> None:
        webhook = str((config or {}).get("webhook") or "").strip()
        if not webhook:
            return
        try:
            validate_outbound_hook_url(webhook, resolve_dns=False)
        except UnsafeOutboundURLError as exc:
            raise serializers.ValidationError({"config": [str(exc)]}) from exc


class RoleSerializer(serializers.ModelSerializer):
    user_count = serializers.SerializerMethodField()

    class Meta:
        model = Role
        fields = ["id", "name", "description", "permissions", "user_count"]
        read_only_fields = ["id", "user_count"]

    def validate_permissions(self, value):
        allowed = get_all_permissions()
        cleaned = []
        for perm in value:
            target = perm
            if target not in allowed and target in PERMISSION_ALIASES:
                target = PERMISSION_ALIASES[target]
            if target not in allowed:
                raise serializers.ValidationError(f"Unsupported permission: {perm}")
            cleaned.append(target)
        return cleaned

    def get_user_count(self, obj):
        return getattr(obj, "user_count", obj.users.count())


class UserRoleSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "display_name",
            "email",
            "roles",
            "auth_source",
            "external_synced_at",
            "is_superuser",
        ]

    def get_roles(self, obj):
        role = get_primary_role(obj)
        return [str(role.id)] if role else []


class LocalUserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, allow_blank=False)
    role_id = serializers.UUIDField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = ["username", "display_name", "email", "password", "role_id"]

    def validate_username(self, value):
        username = (value or "").strip()
        if not username:
            raise serializers.ValidationError("账号不能为空")
        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError("账号已存在")
        return username

    def validate_email(self, value):
        if value is None:
            return ""
        return value.strip()

    def validate_role_id(self, value):
        if value is None:
            return None
        if not Role.objects.filter(id=value).exists():
            raise serializers.ValidationError("角色不存在")
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        role_id = validated_data.pop("role_id", None)
        user = User(**validated_data)
        user.auth_source = "local"
        user.set_password(password)
        user.save()
        if role_id:
            role = Role.objects.get(id=role_id)
            user.roles.set([role])
        return user


class AlertTemplateSerializer(serializers.ModelSerializer):
    channel_label = serializers.SerializerMethodField(read_only=True)
    variables = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = AlertTemplate
        fields = [
            "id",
            "channel_type",
            "channel_label",
            "variables",
            "name",
            "description",
            "subject",
            "body",
            "is_default",
            "updated_at",
        ]
        read_only_fields = ["id", "updated_at", "channel_label"]

    def validate_channel_type(self, value):
        allowed = {definition["type"] for definition in CHANNEL_DEFINITIONS}
        if value not in allowed:
            raise serializers.ValidationError("Unsupported channel type")
        return value

    def validate_body(self, value):
        text = value.strip()
        if not text:
            raise serializers.ValidationError("通知内容不能为空")
        validate_alert_template(text)
        return text

    def create(self, validated_data):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        return AlertTemplate.objects.create(created_by=user, updated_by=user, **validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        request = self.context.get("request")
        if request:
            instance.updated_by = request.user
        instance.save()
        return instance

    def get_channel_label(self, obj):
        mapping = {definition["type"]: definition["name"] for definition in CHANNEL_DEFINITIONS}
        return mapping.get(obj.channel_type, obj.channel_type)

    def get_variables(self, obj):
        return ALERT_VARIABLES
