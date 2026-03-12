from rest_framework import permissions
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.tools.api.serializers import IPRegexCompileSerializer, IPRegexReverseSerializer
from apps.tools.services.ip_regex_runner import IPRegexScriptError, load_ip_regex_runtime


class IPRegexCompileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request) -> Response:
        serializer = IPRegexCompileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ips = serializer.validated_data["ips"]

        try:
            runtime = load_ip_regex_runtime()
        except IPRegexScriptError as exc:
            raise ValidationError({"detail": str(exc)}) from exc

        regex, invalid_ips = runtime.ip_to_regex(ips)
        valid_count = len(ips) - len(invalid_ips)
        if valid_count <= 0:
            raise ValidationError({"ips": ["没有可用的 IP 地址"], "invalid_ips": invalid_ips})

        return Response(
            {
                "regex": regex,
                "matched_count": valid_count,
                "invalid_ips": invalid_ips,
            }
        )


class IPRegexReverseView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request) -> Response:
        serializer = IPRegexReverseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        pattern = serializer.validated_data["pattern"]
        limit = serializer.validated_data["limit"]

        try:
            runtime = load_ip_regex_runtime()
        except IPRegexScriptError as exc:
            raise ValidationError({"detail": str(exc)}) from exc

        try:
            ips = runtime.regex_to_ips(pattern, min(limit, runtime.max_results))
        except runtime.too_complex_error as exc:
            raise ValidationError({"pattern": str(exc)}) from exc
        except runtime.conversion_error as exc:
            raise ValidationError({"pattern": str(exc)}) from exc

        return Response(
            {
                "ips": ips,
                "count": len(ips),
                "limit": min(limit, runtime.max_results),
            }
        )
