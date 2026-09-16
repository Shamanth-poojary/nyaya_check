"""
app/auth.py — Authentication dependency for API-key secured routes.

Implements an X-API-Key header check toggleable via Settings.api_key.
When Settings.api_key is None (the default), auth is completely bypassed.
When set, requests must supply the exact matching key in the X-API-Key header.
"""

from __future__ import annotations

from typing import Optional

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: Optional[str] = Security(api_key_header)) -> Optional[str]:
    """Verify that incoming request provides a valid X-API-Key header if auth is enabled.

    Bypassed when settings.api_key is None or empty.
    """
    if settings.api_key is not None:
        if not api_key or api_key != settings.api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing API key. Provide a valid 'X-API-Key' header.",
            )
    return api_key
