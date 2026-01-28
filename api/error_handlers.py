from fastapi import Request
from fastapi.responses import JSONResponse
import logging

from api.exceptions import TJRSBaseError

logger = logging.getLogger(__name__)


async def tjrs_exception_handler(request: Request, exc: TJRSBaseError):
    logger.warning(
        f"TJRS error | path={request.url.path} | status={exc.status_code} | detail={exc.message}"
    )

    headers = {}
    if hasattr(exc, "retry_after"):
        headers["Retry-After"] = str(exc.retry_after)

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "TJRS_ERROR",
            "detail": exc.message,
        },
        headers=headers,
    )


async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled error | path={request.url.path} | error={exc}")

    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "detail": "Erro interno inesperado",
        },
    )