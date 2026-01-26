class TJRSRateLimit(Exception):
    def __init__(self, message: str, retry_after: int = 10):
        super().__init__(message)
        self.message = message
        self.retry_after = retry_after
