import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """ 
    It will attach a unique ID to every request tht will be sent.
    If the client sends an X-Correlation-ID header, use it, but it they don't generate one and send it back in the response
    """
    
    async def dispatch(self, request: Request, call_next) -> Response:
        correlation_id = (
            request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        )
        
        # Attach to request state so any part of the app can read it
        request.state.correlation_id = correlation_id
        
        response = await call_next(request)
        
        
        # Echo it back so the client can trace their request in your logs
        response.headers["X-Correlation-ID"] = correlation_id
        
        return response
            
            
            