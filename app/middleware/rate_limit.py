import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
import redis.asyncio as aioredis

from app.core.config import settings

logger = logging.getLogger(__name__)


STRICT_PATHS = {"/api/v1/auth/login", "/api/v1/auth/register"}

# Default: 50 requests per minute per IP
DEFAULT_LIMIT = 50
DEFAULT_WINDOW = 60

# Strict: 10 requests per minute per IP
STRICT_LIMIT = 10
STRICT_WINDOW = 60


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Sliding window rate limiter backed by Redis.
    Keyed per IP address with stricter limits on auth routes.
    """

    def __init__(self, app):
        super().__init__(app)
        self.redis = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )

    async def dispatch(self, request: Request, call_next) -> JSONResponse:
        client_ip = self._get_client_ip(request)
        path = request.url.path
        correlation_id = getattr(request.state, "correlation_id", "-")

        is_strict = path in STRICT_PATHS
        limit = STRICT_LIMIT if is_strict else DEFAULT_LIMIT
        window = STRICT_WINDOW if is_strict else DEFAULT_WINDOW

        key = f"rate_limit:{client_ip}:{path if is_strict else 'global'}"

        try:
            current = await self._check_rate_limit(key, window)
        except Exception as e:
            logger.error("Rate limit Redis error: %s", str(e))
            return await call_next(request)

        remaining = max(0, limit - current)

        if current > limit:
            logger.warning(
                "[%s] Rate limit exceeded | IP: %s | Path: %s | Count: %s",
                correlation_id,
                client_ip,
                path,
                current,
            )
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Too many requests. Please slow down.",
                    "code": "RATE_LIMIT_EXCEEDED",
                },
                headers={
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(window),
                    "Retry-After": str(window),
                },
            )

        response = await call_next(request)

        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(window)

        return response

    async def _check_rate_limit(self, key: str, window: int) -> int:
        """
        Sliding window counter using Redis INCR + EXPIRE.
        First request in a window sets the expiry.
        Subsequent requests increment the counter.
        """
        pipe = self.redis.pipeline()
        now = int(time.time())
        await pipe.incr(key)
        await pipe.expire(key, window)
        results = await pipe.execute()
        return results[0] 

    @staticmethod
    def _get_client_ip(request: Request) -> str:
        """
        Respect X-Forwarded-For when behind a load balancer or reverse proxy.
        Falls back to direct connection IP.
        """
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.client.host