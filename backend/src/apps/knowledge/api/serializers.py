from __future__ import annotations

from django.utils.text import slugify
from rest_framework import serializers

from apps.knowledge.models import KnowledgeArticle, KnowledgeArticleVersion, KnowledgeCategory


class KnowledgeCategorySerializer(serializers.ModelSerializer):
    article_count = serializers.SerializerMethodField()

    class Meta:
        model = KnowledgeCategory
        fields = ("key", "title", "description", "builtin", "display_order", "article_count")
        extra_kwargs = {
            "display_order": {"required": False},
            "builtin": {"read_only": True},
        }

    def get_article_count(self, obj) -> int:
        counts = self.context.get("article_counts") or {}
        return counts.get(obj.key, 0)

    def update(self, instance, validated_data):
        validated_data.pop("key", None)
        validated_data.pop("builtin", None)
        return super().update(instance, validated_data)


class KnowledgeArticleSerializer(serializers.ModelSerializer):
    category_label = serializers.SerializerMethodField()

    class Meta:
        model = KnowledgeArticle
        fields = (
            "id",
            "title",
            "slug",
            "category",
            "category_label",
            "tags",
            "content",
            "attachments",
            "visibility_scope",
            "last_edited_at",
        )


    def get_category_label(self, obj) -> str:
        category_map = self.context.get("category_map") or {}
        if obj.category in category_map:
            return category_map[obj.category]
        category = KnowledgeCategory.objects.filter(key=obj.category).first()
        if category:
            return category.title
        return obj.category or "未分类"


class KnowledgeArticleCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgeArticle
        fields = (
            "title",
            "slug",
            "category",
            "tags",
            "content",
            "attachments",
            "visibility_scope",
        )
        extra_kwargs = {
            "slug": {"required": False, "allow_blank": True},
        }

    def validate_category(self, value: str) -> str:
        if not value:
            raise serializers.ValidationError("请选择目录")
        if not KnowledgeCategory.objects.filter(key=value).exists():
            raise serializers.ValidationError("目录不存在，请先在目录管理中创建")
        return value

    def create(self, validated_data):
        self._ensure_slug(validated_data)
        request = self.context.get("request")
        return KnowledgeArticle.objects.create(
            **validated_data,
            created_by=getattr(request, "user", None),
            last_editor=getattr(request, "user", None),
        )

    def update(self, instance, validated_data):
        self._ensure_slug(validated_data, instance=instance)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.last_editor = getattr(self.context.get("request"), "user", None)
        instance.save()
        return instance

    def _ensure_slug(self, validated_data, instance: KnowledgeArticle | None = None):
        slug_value = validated_data.get("slug")
        title = validated_data.get("title") or (instance.title if instance else None)
        if slug_value:
            return
        if not title:
            return
        base = slugify(title) or "article"
        slug_value = base
        idx = 2
        queryset = KnowledgeArticle.objects.all()
        if instance:
            queryset = queryset.exclude(pk=instance.pk)
        while queryset.filter(slug=slug_value).exists():
            slug_value = f"{base}-{idx}"
            idx += 1
        validated_data["slug"] = slug_value


class KnowledgeArticleVersionSerializer(serializers.ModelSerializer):
    editor = serializers.SerializerMethodField()

    class Meta:
        model = KnowledgeArticleVersion
        fields = (
            "id",
            "version",
            "title",
            "category",
            "visibility_scope",
            "tags",
            "content",
            "summary",
            "created_at",
            "editor",
        )

    def get_editor(self, obj):
        if obj.updated_by:
            return obj.updated_by.get_full_name() or obj.updated_by.username
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.username
        return None
