from dataclasses import dataclass


@dataclass
class TJRSBaseError(Exception):
    """Exceção base para erros conhecidos relacionados ao TJRS.
    
    Attributes:
        message (str): Mensagem descritiva do erro.
        status_code (int): Status HTTP associado ao erro.
    """
    message: str = "Erro TJRS"
    status_code: int = 500

    def __str__(self) -> str:
        """Retorna a mensagem legível da exceção.
        
        Returns:
            str: Mensagem configurada para o erro.
        """
        return self.message


@dataclass
class TJRSUnauthorized(TJRSBaseError):
    """Erro de autenticação ou autorização ao acessar o TJRS.
    """
    message: str = "Não autorizado no TJRS"
    status_code: int = 401


@dataclass
class TJRSRateLimit(TJRSBaseError):
    """Erro lançado quando o TJRS limita a quantidade de requisições.
    
    Attributes:
        retry_after (int): Tempo sugerido, em segundos, antes de uma nova tentativa.
    """
    message: str = "Rate limit no TJRS"
    status_code: int = 429
    retry_after: int = 30


@dataclass
class TJRSNetworkError(TJRSBaseError):
    """
    Timeout ou erro de rede ao consultar o TJRS.
    """

    message: str = "Erro de rede ao consultar TJRS"
    status_code: int = 504


@dataclass
class TJRSUpstreamError(TJRSBaseError):
    """
    TJRS respondeu, mas houve erro persistente
    ou resposta inesperada do upstream.
    """

    message: str = "Falha ao consultar TJRS"
    status_code: int = 502


@dataclass
class TJRSParseError(TJRSBaseError):
    """
    Erro ao interpretar a resposta retornada pelo TJRS.
    """

    message: str = "Falha ao interpretar resposta do TJRS"
    status_code: int = 502


@dataclass
class ProcessNotFoundError(TJRSBaseError):
    """
    Processo não encontrado ou sem dados disponíveis.
    """

    message: str = "Processo não encontrado"
    status_code: int = 404
