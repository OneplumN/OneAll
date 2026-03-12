from __future__ import annotations

import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=64, unique=True)
    description = models.TextField(blank=True)
    permissions = models.JSONField(default=list, blank=True)

    class Meta:
        db_table = "core_role"
        verbose_name = "Role"
        verbose_name_plural = "Roles"

    def __str__(self) -> str:  # pragma: no cover - repr utility
        return self.name


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    display_name = models.CharField(max_length=128, blank=True)
    phone = models.CharField(max_length=32, blank=True)
    status = models.CharField(max_length=32, default="active")
    auth_source = models.CharField(max_length=32, default="local")
    external_id = models.CharField(max_length=255, blank=True)
    external_synced_at = models.DateTimeField(null=True, blank=True)
    roles = models.ManyToManyField(Role, related_name="users", blank=True)

    class Meta:
        db_table = "core_user"
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self) -> str:  # pragma: no cover - repr utility
        return self.username
