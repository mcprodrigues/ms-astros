"""Maps domain exceptions to HTTP responses. Internal details never reach clients."""

import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.domain.errors import (
    AstrosError,
    InvalidCatalogError,
    MovieNotFoundError,
    StoreUnavailableError,
)

logger = logging.getLogger(__name__)

_STATUS_BY_ERROR: dict[type[AstrosError], int] = {
    MovieNotFoundError: status.HTTP_404_NOT_FOUND,
    InvalidCatalogError: status.HTTP_422_UNPROCESSABLE_CONTENT,
    StoreUnavailableError: status.HTTP_503_SERVICE_UNAVAILABLE,
}

_PUBLIC_MESSAGE: dict[type[AstrosError], str] = {
    StoreUnavailableError: "Index backend unavailable",
}


async def handle_astros_error(request: Request, exc: AstrosError) -> JSONResponse:
    error_type = type(exc)
    status_code = next(
        (code for cls, code in _STATUS_BY_ERROR.items() if isinstance(exc, cls)),
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
    if status_code >= 500:
        logger.error("%s on %s %s: %s", error_type.__name__, request.method, request.url.path, exc)
    detail = _PUBLIC_MESSAGE.get(error_type, str(exc) if status_code < 500 else None)
    return JSONResponse(status_code=status_code, content={"detail": detail or "Server error"})


async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AstrosError, handle_astros_error)
    app.add_exception_handler(Exception, handle_unexpected_error)
