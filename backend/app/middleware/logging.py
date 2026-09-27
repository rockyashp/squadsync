"""
Asynchronous HTTP request logging and correlation ID middleware.
Measures request duration and logs method, path, status code, and latency.
"""

from collections.abc import Callable
import logging
import time
import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("squadsync.access")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that generates a unique correlation ID (X-Request-ID) for every request,
    tracks processing latency, and emits structured access log entries.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id

        start_time = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            process_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.exception(
                "Unhandled error processing request: %s %s [request_id=%s] in %.2fms",
                request.method,
                request.url.path,
                request_id,
                process_time_ms,
            )
            raise

        process_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time-Ms"] = str(process_time_ms)

        # Log access info (skip noisy health pings in debug/test if desired)
        logger.info(
            "%s %s -> %d %s (%.2fms) [request_id=%s]",
            request.method,
            request.url.path,
            response.status_code,
            response.reason_phrase if hasattr(response, "reason_phrase") else "",
            process_time_ms,
            request_id,
        )

        return response
