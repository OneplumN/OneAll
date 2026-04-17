from __future__ import annotations

from rest_framework import permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import RequirePermission
from apps.monitoring.services.cmdb_checker import validate_domain


class DomainValidationView(APIView):
    permission_classes = [permissions.IsAuthenticated, RequirePermission("detection.oneoff.view")]

    def get(self, request: Request) -> Response:
        domain = request.query_params.get('domain')
        if not domain:
            return Response(
                {'detail': '缺少域名参数'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = validate_domain(domain)
        return Response(
            {
                'status': result.status.value,
                'message': result.message,
                'record': result.record,
            }
        )
