class TJRSRateLimit(Exception):
    def __init__(self, message: str, retry_after: int = 10):
        super().__init__(message)
        self.message = message
        self.retry_after = retry_after
class TJRSBadResponse(Exception):
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
