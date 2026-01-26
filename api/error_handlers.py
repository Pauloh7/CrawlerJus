from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .exceptions import (
    TJRSUnauthorized,
    TJRSRateLimit,
    TJRSUpstreamError,
    TJRSNetworkError,
)

def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(TJRSUnauthorized)
    async def handle_tjrs_unauthorized(request: Request, exc: TJRSUnauthorized):
        return JSONResponse(
            status_code=401,
            content={"detail": exc.message},
        )

    @app.exception_handler(TJRSRateLimit)
    async def handle_tjrs_rate_limit(request: Request, exc: TJRSRateLimit):
        return JSONResponse(
            status_code=429,
            content={"detail": exc.message},
            headers={"Retry-After": str(exc.retry_after)},
        )

    @app.exception_handler(TJRSNetworkError)
    async def handle_tjrs_network(request: Request, exc: TJRSNetworkError):
        return JSONResponse(
            status_code=504, 
            content={"detail": exc.message},
        )

    @app.exception_handler(TJRSUpstreamError)
    async def handle_tjrs_upstream(request: Request, exc: TJRSUpstreamError):
        return JSONResponse(
            status_code=502,
            content={"detail": exc.message},
        )