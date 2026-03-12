from __future__ import annotations

import logging
import time
from typing import Callable

from django.http import HttpRequest, HttpResponse

logger = logging.getLogger("core.performance")


class RequestTimingMiddleware:
    """
    为每个请求添加耗时头，便于在浏览器 Network 中快速定位“慢在后端还是前端”。

    - X-Request-Duration-ms: 后端总耗时（毫秒）
    - Server-Timing: 浏览器可视化展示（Chrome/Edge）
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        start = time.perf_counter()
        response = self.get_response(request)
        duration_ms = (time.perf_counter() - start) * 1000.0

        try:
            response["X-Request-Duration-ms"] = f"{duration_ms:.1f}"
            response["Server-Timing"] = f"app;dur={duration_ms:.1f}"
        except Exception:
            # 某些流式/特殊响应不保证可写 header
            pass

        if duration_ms >= 1000:
            logger.warning(
                "slow_request method=%s path=%s status=%s duration_ms=%.1f",
                request.method,
                getattr(request, "path", ""),
                getattr(response, "status_code", None),
                duration_ms,
            )

        return response

