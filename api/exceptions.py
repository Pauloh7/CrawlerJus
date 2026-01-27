from dataclasses import dataclass


@dataclass
class TJRSBaseError(Exception):
    message: str = "Erro TJRS"

    def __str__(self) -> str:
        return self.message


@dataclass
class TJRSUnauthorized(TJRSBaseError):
    message: str = "Não autorizado no TJRS"


@dataclass
class TJRSRateLimit(TJRSBaseError):
    message: str = "Rate limit no TJRS"
    retry_after: int = 30


@dataclass
class TJRSUpstreamError(TJRSBaseError):
    """
    TJRS respondeu, mas resposta inesperada (HTML, JSON inválido, 5xx persistente etc.)
    """
    message: str = "Falha ao consultar TJRS"


@dataclass
class TJRSNetworkError(TJRSBaseError):
    """
    Timeout/erro de rede para TJRS.
    """
    message: str = "Erro de rede ao consultar TJRS"