"""Rate limiting middleware."""

import time
from typing import Dict, Tuple
from collections import defaultdict
from datetime import datetime, timedelta

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from starlette.status import HTTP_429_TOO_MANY_REQUESTS


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using sliding window."""

    def __init__(
            self,
            app,
            requests_per_minute: int = 60,
            requests_per_hour: int = 1000
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour

        # Store request timestamps by IP
        self.requests: Dict[str, list] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting."""
        # Skip rate limiting for health checks
        if request.url.path == "/health":
            return await call_next(request)

        # Get client IP
        client_ip = request.client.host

        # Check rate limits
        now = time.time()

        # Clean old timestamps
        self._clean_old_timestamps(client_ip, now)

        # Check if rate limit exceeded
        if self._is_rate_limited(client_ip, now):
            return JSONResponse(
                status_code=HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "Too many requests. Please try again later."
                    }
                },
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(self.requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(now + 60))
                }
            )

        # Record this request
        self.requests[client_ip].append(now)

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        remaining = self.requests_per_minute - len(self.requests[client_ip])
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        response.headers["X-RateLimit-Reset"] = str(int(now + 60))

        return response

    def _clean_old_timestamps(self, client_ip: str, now: float):
        """Remove timestamps older than 1 hour."""
        one_hour_ago = now - 3600
        self.requests[client_ip] = [
            ts for ts in self.requests[client_ip]
            if ts > one_hour_ago
        ]

    def _is_rate_limited(self, client_ip: str, now: float) -> bool:
        """Check if client has exceeded rate limits."""
        timestamps = self.requests[client_ip]

        # Check per-minute limit
        one_minute_ago = now - 60
        recent_requests = sum(1 for ts in timestamps if ts > one_minute_ago)
        if recent_requests >= self.requests_per_minute:
            return True

        # Check per-hour limit
        if len(timestamps) >= self.requests_per_hour:
            return True

        return False