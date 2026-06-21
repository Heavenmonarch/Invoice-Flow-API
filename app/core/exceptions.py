import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

logger = logging.getLogger(__name__)


# standard response
def error_response(status_code: int, message: str, code: str = None) -> JSONResponse:
    content = {"detail": message}
    if code:
        content["code"] = code
    return JSONResponse(status_code=status_code, content=content)

# custom response
class AppException(Exception):
    def __init__(
        self,
        status_code: int,
        detail: str,
        code: str = None,
    ):
        self.status_code = status_code
        self.detail = detail
        self.code = code


class NotFoundException(AppException):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail, code="NOT_FOUND")


class ConflictException(AppException):
    def __init__(self, detail: str = "Resource already exists"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail, code="CONFLICT")


class ForbiddenException(AppException):
    def __init__(self, detail: str = "Access denied"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail, code="FORBIDDEN")


class UnauthorizedException(AppException):
    def __init__(self, detail: str = "Authentication required"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail, code="UNAUTHORIZED")


class BadRequestException(AppException):
    def __init__(self, detail: str = "Bad request"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail, code="BAD_REQUEST")


class UnprocessableException(AppException):
    def __init__(self, detail: str = "Unprocessable request"):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            code="UNPROCESSABLE",
        )


# handler registration
def register_exception_handlers(app: FastAPI) -> None:

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        logger.warning(
            "AppException | %s %s | %s | %s",
            request.method,
            request.url.path,
            exc.status_code,
            exc.detail,
        )
        return error_response(exc.status_code, exc.detail, exc.code)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """
        Pydantic validation errors — field-level detail flattened
        into a single readable message.
        """
        errors = []
        for error in exc.errors():
            field = " -> ".join(str(loc) for loc in error["loc"] if loc != "body")
            errors.append(f"{field}: {error['msg']}" if field else error["msg"])

        message = "; ".join(errors)
        logger.info(
            "ValidationError | %s %s | %s",
            request.method,
            request.url.path,
            message,
        )
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message=message,
            code="VALIDATION_ERROR",
        )

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError):
        """
        Database constraint violations — unique constraints,
        foreign key violations, not-null violations.
        """
        logger.error(
            "IntegrityError | %s %s | %s",
            request.method,
            request.url.path,
            str(exc.orig),
        )
        # Parse the most common Postgres constraint errors
        orig = str(exc.orig).lower()
        if "unique" in orig:
            return error_response(
                status_code=status.HTTP_409_CONFLICT,
                message="A record with this value already exists",
                code="DUPLICATE_ENTRY",
            )
        if "foreign key" in orig:
            return error_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Referenced resource does not exist",
                code="FOREIGN_KEY_VIOLATION",
            )
        if "not null" in orig:
            return error_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="A required field is missing",
                code="NULL_VIOLATION",
            )
        return error_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="Database constraint violation",
            code="INTEGRITY_ERROR",
        )

    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError):
        """
        Any other database error — connection failures,
        timeouts, query errors.
        """
        logger.error(
            "SQLAlchemyError | %s %s | %s",
            request.method,
            request.url.path,
            str(exc),
            exc_info=True,
        )
        return error_response(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            message="A database error occurred. Please try again shortly.",
            code="DATABASE_ERROR",
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        """
        Catch-all for anything not handled above.
        Logs full traceback internally, returns safe message to client.
        """
        logger.error(
            "UnhandledException | %s %s | %s",
            request.method,
            request.url.path,
            str(exc),
            exc_info=True,
        )
        return error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="An unexpected error occurred. Our team has been notified.",
            code="INTERNAL_ERROR",
        )