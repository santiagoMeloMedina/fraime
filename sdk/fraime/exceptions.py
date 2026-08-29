class FraimeError(Exception):
    """Base class for all Fraime SDK errors."""


class FraimeConnectionError(FraimeError):
    """The API couldn't be reached at all (network/DNS/timeout)."""


class FraimeAuthError(FraimeError):
    """The API rejected the request due to a missing or invalid API key."""


class FraimeAPIError(FraimeError):
    """The API reached and responded, but with an error status."""

    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"Fraime API returned {status_code}: {detail}")
