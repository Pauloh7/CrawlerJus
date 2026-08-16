import logging

from fastapi import Request
from fastapi.responses import JSONResponse

from api.exceptions import TJRSBaseError
from api.request_context import request_id_context

logger = logging.getLogger(__name__)


async def tjrs_exception_handler(
    request: Request,
    exc: TJRSBaseError,
):
    """Converte erros conhecidos do TJRS em respostas HTTP padronizadas.
    
    Args:
        request (Request): Requisição que originou o erro.
        exc (TJRSBaseError): Exceção conhecida da aplicação.
    
    Returns:
        JSONResponse: Resposta com status e detalhes definidos pela exceção.
    """
    request_id = request_id_context.get()

    logger.warning(
        "tjrs_error",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "error_type": type(exc).__name__,
            "status_code": exc.status_code,
        },
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": type(exc).__name__,
            "detail": str(exc),
            "request_id": request_id,
        },
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception,
):
    """Trata exceções inesperadas sem expor detalhes internos ao cliente.
    
    Args:
        request (Request): Requisição que originou o erro.
        exc (Exception): Exceção não tratada por handlers específicos.
    
    Returns:
        JSONResponse: Resposta HTTP 500 com mensagem genérica.
    """
    request_id = request_id_context.get()

    logger.exception(
        "unhandled_error",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "error_type": type(exc).__name__,
        },
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "detail": "Erro interno inesperado",
            "request_id": request_id,
        },
    )
