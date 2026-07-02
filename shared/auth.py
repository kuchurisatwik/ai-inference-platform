"""Tiny API-key auth shared by both services.

Callers must send an `X-API-Key` header matching one of the configured keys.
If no keys are configured, auth is OFF (handy for local dev / mock mode).
"""
from fastapi import Header, HTTPException, status


def check_api_key(provided: str | None, valid_keys: set[str]) -> None:
    """Raise 401 unless `provided` is one of `valid_keys`.

    An empty `valid_keys` set means auth is disabled — everything is allowed.
    """
    if not valid_keys:
        return
    if not provided or provided not in valid_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key (send it in the 'X-API-Key' header)",
        )
