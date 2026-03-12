from __future__ import annotations

import json

from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.text import slugify
from django.utils.html import strip_tags
from rest_framework import permissions, status
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.knowledge.api.serializers import (
    KnowledgeArticleCreateSerializer,
    KnowledgeArticleSerializer,
    KnowledgeArticleVersionSerializer,
    KnowledgeCategorySerializer,
)
from apps.knowledge.models import KnowledgeArticle, KnowledgeArticleVersion, KnowledgeCategory
from apps.knowledge.services.article_importer import convert_uploaded_file


def _category_map() -> dict[str, str]:
    return {key: title for key, title in KnowledgeCategory.objects.values_list("key", "title")}


def _category_counts() -> dict[str, int]:
    return {
        row["category"]: row["total"]
        for row in KnowledgeArticle.objects.values("category").annotate(total=Count("id"))
    }


def _ensure_default_category() -> KnowledgeCategory:
    category, _ = KnowledgeCategory.objects.get_or_create(
        key="uncategorized",
        defaults={"title": "未分类", "description": "默认目录", "display_order": 9999},
    )
    return category


def _prepare_article_payload(request: Request, partial: bool = False):
    """
    Prepare incoming data for create/update, handling multipart uploads.
    Returns (mutable_data, metadata_extra).
    """
    query_data = request.data
    if hasattr(query_data, "keys"):
        payload = {key: query_data.get(key) for key in query_data.keys()}
    else:
        payload = dict(query_data)

    # Normalize tags (JSONField expects list)
    tags_list: list[str] | None = None
    if hasattr(request.data, "getlist"):
        for key in ("tags", "tags[]"):
            values = request.data.getlist(key)
            if values:
                tags_list = values
                # remove alternates from payload to avoid serializer confusion
                if hasattr(payload, "pop"):
                    payload.pop(key, None)
                break

    if tags_list is None:
        raw_tags = query_data.get("tags") or query_data.get("tags[]") or payload.get("tags")
        if isinstance(raw_tags, str):
            raw = raw_tags.strip()
            if raw:
                try:
                    parsed = json.loads(raw)
                    if isinstance(parsed, list):
                        tags_list = parsed
                    else:
                        tags_list = [raw]
                except json.JSONDecodeError:
                    tags_list = [raw]
        elif isinstance(raw_tags, list):
            tags_list = raw_tags
    if tags_list is not None:
        payload["tags"] = tags_list

    upload = request.FILES.get("source_file")
    metadata_extra = None

    if upload:
        content_html = convert_uploaded_file(upload)
        payload["content"] = content_html
        metadata_extra = {
            "source": {
                "filename": upload.name,
                "content_type": upload.content_type,
                "size": upload.size,
                "uploaded_at": timezone.now().isoformat(),
            }
        }
        if hasattr(payload, "pop"):
            payload.pop("source_file", None)
    elif not partial and not payload.get("content"):
        raise ValidationError("请上传文件或填写正文内容")

    return payload, metadata_extra


def _record_article_version(article: KnowledgeArticle, user=None) -> KnowledgeArticleVersion:
    last_version = article.versions.order_by("-version").first()
    next_version = (last_version.version if last_version else 0) + 1
    summary = strip_tags(article.content or "")[:200]
    version = KnowledgeArticleVersion.objects.create(
        article=article,
        version=next_version,
        title=article.title,
        slug=article.slug,
        category=article.category,
        tags=article.tags,
        visibility_scope=article.visibility_scope,
        content=article.content,
        summary=summary,
        created_by=user,
        updated_by=user,
    )
    return version


class KnowledgeArticleListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def get(self, request: Request) -> Response:
        queryset = KnowledgeArticle.objects.order_by("-last_edited_at")
        keyword = request.query_params.get("keyword")
        category = request.query_params.get("category")
        scope = request.query_params.get("scope")
        tag = request.query_params.get("tag")

        if keyword:
            from django.db.models import Q

            queryset = queryset.filter(Q(title__icontains=keyword) | Q(content__icontains=keyword))
        if tag:
            queryset = queryset.filter(tags__contains=[tag])
        if category:
            queryset = queryset.filter(category=category)
        if scope:
            queryset = queryset.filter(visibility_scope=scope)

        serializer = KnowledgeArticleSerializer(queryset, many=True, context={"category_map": _category_map()})
        return Response(serializer.data)

    def post(self, request: Request) -> Response:
        payload, source_meta = _prepare_article_payload(request)
        serializer = KnowledgeArticleCreateSerializer(data=payload, context={"request": request})
        serializer.is_valid(raise_exception=True)
        article = serializer.save()
        if source_meta:
            article.metadata = {**(article.metadata or {}), **source_meta}
            article.save(update_fields=["metadata"])
        _record_article_version(article, request.user)
        return Response(
            KnowledgeArticleSerializer(article, context={"category_map": _category_map()}).data,
            status=status.HTTP_201_CREATED,
        )


class KnowledgeArticleDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, slug: str) -> KnowledgeArticle:
        article = KnowledgeArticle.objects.filter(slug=slug).first()
        if article:
            return article
        # Fallback to UUID/id lookup if slug missing
        try:
            return KnowledgeArticle.objects.get(id=slug)
        except (KnowledgeArticle.DoesNotExist, ValueError):
            raise Http404

    def get(self, request: Request, slug: str) -> Response:
        article = self.get_object(slug)
        return Response(KnowledgeArticleSerializer(article, context={"category_map": _category_map()}).data)

    def put(self, request: Request, slug: str) -> Response:
        article = self.get_object(slug)
        payload, source_meta = _prepare_article_payload(request, partial=True)
        serializer = KnowledgeArticleCreateSerializer(
            article,
            data=payload,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        article = serializer.save()
        if source_meta:
            article.metadata = {**(article.metadata or {}), **source_meta}
            article.save(update_fields=["metadata"])
        _record_article_version(article, request.user)
        return Response(KnowledgeArticleSerializer(article, context={"category_map": _category_map()}).data)

    def delete(self, request: Request, slug: str) -> Response:
        article = self.get_object(slug)
        article.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class KnowledgeArticleVersionListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request, slug: str) -> Response:
        try:
            article = KnowledgeArticle.objects.filter(slug=slug).first()
            if not article:
                article = KnowledgeArticle.objects.get(id=slug)
        except (KnowledgeArticle.DoesNotExist, ValueError):
            raise Http404
        versions = article.versions.order_by("-version")
        serializer = KnowledgeArticleVersionSerializer(versions, many=True)
        return Response(serializer.data)


class KnowledgeCategoryListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request) -> Response:
        categories = KnowledgeCategory.objects.order_by("display_order", "title")
        serializer = KnowledgeCategorySerializer(
            categories,
            many=True,
            context={"article_counts": _category_counts()},
        )
        return Response(serializer.data)

    def post(self, request: Request) -> Response:
        payload = request.data.copy()
        title = (payload.get("title") or "").strip()
        if not payload.get("key"):
            payload["key"] = slugify(title) or slugify(payload.get("description") or "category")
        if "display_order" not in payload:
            payload["display_order"] = KnowledgeCategory.objects.count()
        serializer = KnowledgeCategorySerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        category = serializer.save()
        data = KnowledgeCategorySerializer(
            category,
            context={"article_counts": _category_counts()},
        ).data
        return Response(data, status=status.HTTP_201_CREATED)


class KnowledgeCategoryDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, key: str) -> KnowledgeCategory:
        return get_object_or_404(KnowledgeCategory, key=key)

    def put(self, request: Request, key: str) -> Response:
        category = self.get_object(key)
        serializer = KnowledgeCategorySerializer(
            category,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        data = KnowledgeCategorySerializer(
            category,
            context={"article_counts": _category_counts()},
        ).data
        return Response(data)

    patch = put

    def delete(self, request: Request, key: str) -> Response:
        category = self.get_object(key)
        if category.builtin:
            return Response({"detail": "内置目录不可删除"}, status=status.HTTP_400_BAD_REQUEST)
        fallback = _ensure_default_category()
        KnowledgeArticle.objects.filter(category=category.key).update(category=fallback.key)
        category.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class KnowledgeCategoryOrderView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request) -> Response:
        keys = request.data.get("keys") or []
        if not isinstance(keys, list) or not keys:
            return Response({"detail": "keys must be a non-empty list"}, status=status.HTTP_400_BAD_REQUEST)

        existing_keys = list(KnowledgeCategory.objects.filter(key__in=keys).values_list("key", flat=True))
        order_map = {key: idx for idx, key in enumerate(keys) if key in existing_keys}
        if not order_map:
            return Response({"detail": "无有效目录"}, status=status.HTTP_400_BAD_REQUEST)

        for key, order in order_map.items():
            KnowledgeCategory.objects.filter(key=key).update(display_order=order)

        return Response(
            KnowledgeCategorySerializer(
                KnowledgeCategory.objects.order_by("display_order", "title"),
                many=True,
                context={"article_counts": _category_counts()},
            ).data
        )
