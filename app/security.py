from secrets import compare_digest

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.dependencies import get_settings
from app.settings import Settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(
    provided: str | None = Security(api_key_header),
    settings: Settings = Depends(get_settings),
) -> None:
    """Guard for write and destructive routes. Fails closed when no key is configured."""
    if settings.API_KEY is None or not settings.API_KEY.get_secret_value():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Write operations are disabled: API_KEY is not configured",
        )
    if provided is None or not compare_digest(
        provided.encode(), settings.API_KEY.get_secret_value().encode()
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
