import logging

from fastapi import Request
from fastapi.responses import JSONResponse

from api.exceptions import TJRSBaseError

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
    logger.warning(
        "Erro conhecido ao processar requisição TJRS",
        extra={
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
    logger.exception(
        "Erro não tratado na API",
        extra={
            "path": request.url.path,
            "error_type": type(exc).__name__,
        },
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "detail": "Erro interno inesperado",
        },
    )
