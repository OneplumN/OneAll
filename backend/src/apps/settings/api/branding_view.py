from __future__ import annotations

from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.settings.services.system_settings_service import get_system_settings


class PublicBrandingView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request: Request) -> Response:
        settings_obj = get_system_settings()
        return Response(
            {
                "platform_name": settings_obj.platform_name,
                "platform_logo": settings_obj.platform_logo,
                "theme": settings_obj.theme,
            }
        )

