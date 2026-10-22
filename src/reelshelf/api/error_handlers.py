import logging
from collections.abc import Mapping
from http import HTTPStatus

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse

from reelshelf.domain.errors import (
    BusinessRuleError,
    ConflictError,
    DomainError,
    NotFoundError,
    UnauthorizedError,
)
from reelshelf.schemas.errors import ErrorDetail, ErrorResponse

logger = logging.getLogger(__name__)


def error_response(
    *,
    status_code: int,
    code: str,
    message: str,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    body = ErrorResponse(
        error=ErrorDetail(
            code=code,
            message=message,
        )
    )

    return JSONResponse(
        status_code=status_code,
        content=body.model_dump(mode="json"),
        headers=headers,
    )


async def handle_domain_error(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    if isinstance(exc, NotFoundError):
        return error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="NOT_FOUND",
            message=exc.message,
        )

    if isinstance(exc, ConflictError):
        return error_response(
            status_code=status.HTTP_409_CONFLICT,
            code="CONFLICT",
            message=exc.message,
        )

    if isinstance(exc, UnauthorizedError):
        return error_response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="UNAUTHORIZED",
            message=exc.message,
            headers={"WWW-Authenticate": "Bearer"},
        )

    if isinstance(exc, BusinessRuleError):
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=exc.message,
        )

    return await handle_unexpected_error(request, exc)


async def handle_request_validation_error(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    return error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        code="VALIDATION_ERROR",
        message="Request validation failed.",
    )


async def handle_http_error(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    if not isinstance(exc, StarletteHTTPException):
        return await handle_unexpected_error(request, exc)

    if exc.status_code >= status.HTTP_500_INTERNAL_SERVER_ERROR:
        return await handle_unexpected_error(request, exc)

    try:
        http_status = HTTPStatus(exc.status_code)
    except ValueError:
        code = "HTTP_ERROR"
        message = "Request failed."
    else:
        code = http_status.name
        message = f"{http_status.phrase}."

    return error_response(
        status_code=exc.status_code,
        code=code,
        message=message,
        headers=exc.headers,
    )


async def handle_unexpected_error(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    logger.error(
        "Unhandled application error",
        exc_info=(type(exc), exc, exc.__traceback__),
    )

    return error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        code="INTERNAL_ERROR",
        message="An unexpected error occurred.",
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(DomainError, handle_domain_error)
    app.add_exception_handler(
        RequestValidationError,
        handle_request_validation_error,
    )
    app.add_exception_handler(StarletteHTTPException, handle_http_error)
    app.add_exception_handler(Exception, handle_unexpected_error)
