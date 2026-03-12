"""Core package for OneAll backend."""

from .celery import celery_app as celery_app

__all__ = ["celery_app"]
