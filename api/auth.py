import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader

from api.config import environment

_authorization_header = APIKeyHeader(name="Authorization", auto_error=False)


def require_api_key(authorization: str | None = Depends(_authorization_header)) -> None:
    expected = environment.auth.api_key
    if expected is None:
        return  # unset AUTH_API_KEY means auth is off, not "reject everything"

    provided = authorization.removeprefix("Bearer ").strip() if authorization else ""
    if not provided or not secrets.compare_digest(provided, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
