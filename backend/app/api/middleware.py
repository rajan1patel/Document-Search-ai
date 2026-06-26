"""
Request Logging Middleware

Logs every API request (method, path, body) and response (status, timing, size).

Format:
  → REQUEST: POST /experts/search
    BODY: {"query": "...", "top_k": 5}
  ← ✅ RESPONSE: 200 /experts/search (4.52s, 2.1KB)
    RESPONSE BODY: {"query": "...", "experts": [...]}
"""
from __future__ import annotations

import logging
import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware that logs every request and response."""

    async def dispatch(self, request: Request, call_next):
        method = request.method
        path = request.url.path

        # ── Log request ──
        body = ""
        try:
            body_bytes = await request.body()
            if body_bytes:
                body = body_bytes.decode("utf-8", errors="replace")[:1000]
        except Exception:
            pass

        logger.info("→ REQUEST: %s %s", method, path)
        if body:
            # Truncate long bodies for readability
            body_display = body if len(body) < 500 else body[:500] + "..."
            logger.info("  BODY: %s", body_display)

        # ── Process request ──
        start_time = time.time()
        try:
            response: Response = await call_next(request)
        except Exception as exc:
            elapsed = time.time() - start_time
            logger.error(
                "← ❌ ERROR: %s %s (%.2fs) — %s",
                method, path, elapsed, exc,
            )
            raise

        elapsed = time.time() - start_time

        # ── Log response ──
        status = response.status_code
        status_icon = "✅" if status < 400 else "⚠️" if status < 500 else "❌"

        # Estimate response size
        resp_body = ""
        try:
            # Check if response has body
            if hasattr(response, "body"):
                resp_body = response.body.decode("utf-8", errors="replace") if response.body else ""
        except Exception:
            pass

        size_kb = len(resp_body) / 1024 if resp_body else 0

        logger.info(
            "← %s RESPONSE: %s %s (%.2fs, %.1fKB)",
            status_icon, status, path, elapsed, size_kb,
        )

        if resp_body and len(resp_body) < 2000:
            logger.info("  RESPONSE BODY: %s", resp_body[:500])

        return response
