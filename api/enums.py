from enum import Enum


class HealthStatus(str, Enum):
    OK = "ok"
    DOWN = "down"
    DEGRADED = "degraded"