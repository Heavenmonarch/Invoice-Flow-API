import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


logger = logging.getLogger(__name__)


# routes that don't need to be logged
EXCLUDED_PATHS = {"/health", "/docs", "/redoc", "/openapi.json"}


class RequestLoggingMiddlewre(BaseHTTPMiddleware):
    """
    Logs every request with method, path, status code, duration and correlation ID
    """
    
    async def dispatch(self, request: Request, call_next) -> Response :
        if request.url.path in EXCLUDED_PATHS:
            return await call_next(request)
        
        
        correlation_id = getattr(request.state, "correlation_id", "-")
        start_time = time.perf_counter()
        
        
        logger.info(
            "[%s] --> %s %s",
            correlation_id,
            request.method,
            request.url.path
        )
        
        try:
            response = await call_next(request)
        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                "[%s] !!! %s %s - UNHANDLED ERROR in %.2fms | %s",
                correlation_id,
                request.method,
                request.url.path,
                duration_ms,
                str(exc),
                exc_info=True,
            )
            raise
        
        duration_ms = (time.perf_counter() - start_time) * 1000
        log_fn = logger.warning if response.status_code >= 400 else logger.info
        
        log_fn(
            "[%s] <-- %s %s - %s in %.2fms",
            correlation_id,
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        
        #Adding duration to response headers for client-side visibility
        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
        return response