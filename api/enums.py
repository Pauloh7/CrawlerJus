from enum import Enum


class HealthStatus(str, Enum):
    """Estados possíveis retornados pelo endpoint de healthcheck.
    
    Values:
        OK: Serviço disponível.
        DOWN: Serviço indisponível.
        DEGRADED: API disponível com dependência externa degradada.
    """
    OK = "ok"
    DOWN = "down"
    DEGRADED = "degraded"
