from dataclasses import dataclass

@dataclass
class TJRSBaseError(Exception):
    message: str = "Erro TJRS"
    status_code: int = 500

    def __str__(self) -> str:
        return self.message


@dataclass
class TJRSUnauthorized(TJRSBaseError):
    message: str = "Não autorizado no TJRS"
    status_code: int = 401


@dataclass
class TJRSRateLimit(TJRSBaseError):
    message: str = "Rate limit no TJRS"
    status_code: int = 429
    retry_after: int = 30


@dataclass
class TJRSNetworkError(TJRSBaseError):
    """
    Timeout/erro de rede para TJRS.
    """
    message: str = "Erro de rede ao consultar TJRS"
    status_code: int = 504


@dataclass
class TJRSUpstreamError(TJRSBaseError):
    """
    TJRS respondeu, mas resposta inesperada (HTML, JSON inválido, 5xx persistente etc.)
    """
    message: str = "Falha ao consultar TJRS"
    status_code: int = 502