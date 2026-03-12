from __future__ import annotations

from django.conf import settings
from django.utils.text import slugify
from rest_framework import serializers

from apps.tools.models import (
    CodeDirectory,
    CodeRepository,
    CodeRepositoryVersion,
    ScriptPlugin,
    ScriptVersion,
    ToolDefinition,
    ToolExecution,
)
from apps.tools.services.script_repository import ScriptRepositoryService

MAX_REVERSE_RESULTS = getattr(settings, "IP_REGEX_MAX_RESULTS", 2000)


class ScriptVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScriptVersion
        fields = (
            "id",
            "version",
            "language",
            "repository_path",
            "checksum",
            "created_at",
        )


class ToolDefinitionSerializer(serializers.ModelSerializer):
    latest_version = ScriptVersionSerializer(read_only=True)

    class Meta:
        model = ToolDefinition
        fields = (
            "id",
            "name",
            "category",
            "tags",
            "description",
            "entry_point",
            "default_parameters",
            "latest_version",
            "created_at",
            "updated_at",
        )


class ToolCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150)
    category = serializers.CharField(max_length=100)
    tags = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    description = serializers.CharField(required=False, allow_blank=True)
    entry_point = serializers.CharField(required=False, allow_blank=True)
    default_parameters = serializers.JSONField(required=False)
    language = serializers.ChoiceField(choices=ScriptVersion.Language.choices, default=ScriptVersion.Language.PYTHON)
    content = serializers.CharField()

    def create(self, validated_data):
        service = ScriptRepositoryService(actor=self.context.get("request").user if self.context.get("request") else None)
        return service.create_tool(
            name=validated_data["name"],
            category=validated_data["category"],
            tags=validated_data.get("tags"),
            description=validated_data.get("description", ""),
            entry_point=validated_data.get("entry_point", ""),
            default_parameters=validated_data.get("default_parameters"),
            initial_script=validated_data["content"],
            language=validated_data.get("language", ScriptVersion.Language.PYTHON),
        )


class ToolExecuteSerializer(serializers.Serializer):
    parameters = serializers.JSONField(required=False)
    script_version_id = serializers.UUIDField(required=False)
    knowledge_slug = serializers.CharField(required=False, allow_blank=True)
    knowledge_title = serializers.CharField(required=False, allow_blank=True)

    def validate_script_version_id(self, value):
        try:
            return ScriptVersion.objects.get(id=value)
        except ScriptVersion.DoesNotExist as exc:  # pragma: no cover - validation branch
            raise serializers.ValidationError("Script version not found") from exc


class ToolExecutionSerializer(serializers.ModelSerializer):
    tool = ToolDefinitionSerializer(read_only=True)
    script_version = ScriptVersionSerializer(read_only=True)

    class Meta:
        model = ToolExecution
        fields = (
            "id",
            "run_id",
            "tool",
            "script_version",
            "status",
            "parameters",
            "output",
            "error_message",
            "started_at",
            "finished_at",
            "created_at",
            "metadata",
        )


class ScriptVersionCreateSerializer(serializers.Serializer):
    language = serializers.ChoiceField(choices=ScriptVersion.Language.choices, default=ScriptVersion.Language.PYTHON)
    repository_path = serializers.CharField(required=False, allow_blank=True)
    content = serializers.CharField()
    metadata = serializers.JSONField(required=False)
    version = serializers.CharField(required=False, allow_blank=True)

    def create(self, validated_data):
        tool: ToolDefinition = self.context["tool"]
        service = ScriptRepositoryService(actor=self.context.get("request").user if self.context.get("request") else None)
        return service.create_version(
            tool,
            content=validated_data["content"],
            language=validated_data.get("language", ScriptVersion.Language.PYTHON),
            repository_path=validated_data.get("repository_path", ""),
            metadata=validated_data.get("metadata"),
            version=validated_data.get("version") or None,
        )


def slugify_title(title: str) -> str:
    base = slugify(title) or "article"
    return base[:200]


class CodeDirectorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CodeDirectory
        fields = ("key", "title", "description", "keywords", "builtin", "created_at", "updated_at")


class CodeDirectoryWriteSerializer(serializers.ModelSerializer):
    key = serializers.CharField(read_only=True)

    class Meta:
        model = CodeDirectory
        fields = ("key", "title", "description", "keywords")

    def create(self, validated_data):
        base_key = slugify(validated_data.get("title", "")) or "directory"
        key = base_key
        index = 1
        while CodeDirectory.objects.filter(key=key).exists():
            index += 1
            key = f"{base_key}-{index}"
        validated_data["key"] = key[:60]
        return CodeDirectory.objects.create(**validated_data)


class CodeRepositoryVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CodeRepositoryVersion
        fields = ("id", "version", "summary", "change_log", "content", "created_at")


class CodeRepositorySerializer(serializers.ModelSerializer):
    directory = serializers.SlugRelatedField(read_only=True, slug_field="key")
    latest_version = serializers.SerializerMethodField()

    class Meta:
        model = CodeRepository
        fields = (
            "id",
            "name",
            "language",
            "tags",
            "description",
            "directory",
            "latest_version",
            "content",
            "updated_at",
        )

    def get_latest_version(self, obj: CodeRepository):
        return obj.latest_version.version if obj.latest_version else None


class CodeRepositoryWriteSerializer(serializers.ModelSerializer):
    directory = serializers.SlugRelatedField(slug_field="key", queryset=CodeDirectory.objects.all())
    change_log = serializers.CharField(required=False, allow_blank=True, write_only=True)
    version = serializers.CharField(required=False, allow_blank=True, write_only=True)

    class Meta:
        model = CodeRepository
        fields = ("name", "language", "tags", "description", "directory", "content", "change_log", "version")

    def create(self, validated_data):
        change_log = validated_data.pop("change_log", "")
        version_label = validated_data.pop("version", "") or "v1.0.0"
        repository = CodeRepository.objects.create(**validated_data)
        version = CodeRepositoryVersion.objects.create(
            repository=repository,
            version=version_label,
            summary="初始化脚本",
            change_log=change_log or "初始化版本",
            content=repository.content,
        )
        repository.latest_version = version
        repository.save(update_fields=["latest_version"])
        return repository

    def update(self, instance: CodeRepository, validated_data):
        for field in ("name", "language", "tags", "description", "directory", "content"):
            if field in validated_data:
                setattr(instance, field, validated_data[field])
        instance.save()
        return instance


class CodeRepositoryVersionCreateSerializer(serializers.Serializer):
    version = serializers.CharField(required=False, allow_blank=True)
    summary = serializers.CharField(required=False, allow_blank=True)
    change_log = serializers.CharField(required=False, allow_blank=True)
    content = serializers.CharField()


class ScriptPluginSerializer(serializers.ModelSerializer):
    repository_name = serializers.CharField(source="repository.name", read_only=True)
    repository_version_label = serializers.CharField(source="repository_version.version", read_only=True)
    runtime_script = serializers.SerializerMethodField()
    metadata = serializers.SerializerMethodField()

    class Meta:
        model = ScriptPlugin
        fields = [
            "id",
            "slug",
            "name",
            "description",
            "summary",
            "group",
            "route",
            "component",
            "builtin",
            "is_enabled",
            "metadata",
            "repository",
            "repository_version",
            "repository_name",
            "repository_version_label",
            "runtime_script",
        ]
        read_only_fields = [
            "id",
            "repository_name",
            "repository_version_label",
            "runtime_script",
        ]

    def get_runtime_script(self, obj: ScriptPlugin) -> str | None:
        metadata = obj.metadata or {}
        return metadata.get("runtime_script")

    def get_metadata(self, obj: ScriptPlugin) -> dict:
        raw = obj.metadata or {}
        return _sanitize_plugin_metadata(raw, include_secrets=False)


class ScriptPluginUpdateSerializer(serializers.ModelSerializer):
    metadata = serializers.JSONField(required=False)

    class Meta:
        model = ScriptPlugin
        fields = [
            "is_enabled",
            "repository_version",
            "route",
            "component",
            "summary",
            "metadata",
        ]

    def update(self, instance: ScriptPlugin, validated_data):
        metadata = validated_data.pop("metadata", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if metadata is not None:
            instance.metadata = _merge_plugin_metadata(instance.metadata or {}, metadata)
        instance.save()
        return instance


SECRET_MASK = "******"


def _is_secret_key(key: str) -> bool:
    normalized = (key or "").lower()
    return any(part in normalized for part in ("password", "token", "secret", "pwd", "passwd"))


def _sanitize_plugin_metadata(metadata: dict, *, include_secrets: bool) -> dict:
    result = dict(metadata or {})
    config_values = dict(result.get("config_values") or {})
    if not config_values:
        result["config_values"] = config_values
        return result

    if not include_secrets:
        for key, value in list(config_values.items()):
            if _is_secret_key(key) and value not in (None, ""):
                config_values[key] = SECRET_MASK
    result["config_values"] = config_values
    return result


def _merge_plugin_metadata(current: dict, incoming: dict) -> dict:
    merged = dict(current or {})
    incoming_dict = dict(incoming or {})

    incoming_config_values = incoming_dict.pop("config_values", None)
    if isinstance(incoming_config_values, dict):
        current_config_values = dict(merged.get("config_values") or {})
        for key, value in incoming_config_values.items():
            if _is_secret_key(str(key)) and value == SECRET_MASK:
                continue
            current_config_values[str(key)] = value
        merged["config_values"] = current_config_values

    merged.update(incoming_dict)
    return merged


class IPRegexCompileSerializer(serializers.Serializer):
    ips = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=False,
        max_length=500,
        help_text="IP 地址列表，最多 500 个",
    )

    def validate_ips(self, value):
        cleaned = [item.strip() for item in value if item and item.strip()]
        if not cleaned:
            raise serializers.ValidationError("请至少提供一个有效的 IP 地址")
        return cleaned[:500]


class IPRegexReverseSerializer(serializers.Serializer):
    pattern = serializers.CharField()
    limit = serializers.IntegerField(required=False, min_value=1, max_value=MAX_REVERSE_RESULTS)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        attrs.setdefault("limit", MAX_REVERSE_RESULTS)
        return attrs
