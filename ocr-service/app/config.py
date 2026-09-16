"""
app/config.py — Central configuration management using pydantic-settings.

Consolidates operational limits, CORS policies, authentication keys, and
runtime defaults into an environment-driven settings model.
"""

from __future__ import annotations

import json
from typing import List, Optional, Set, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime service configuration settings loaded from environment or .env file."""

    max_images_per_request: int = 10
    max_file_size_mb: int = 15
    allowed_content_types: Set[str] = {"image/jpeg", "image/png", "image/webp"}
    preprocess_enabled_default: bool = False
    api_key: Optional[str] = None  # None or empty string = authentication disabled
    cors_allowed_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]
    log_level: str = "INFO"
    web_concurrency: int = 2

    @field_validator("api_key", mode="before")
    @classmethod
    def _normalize_api_key(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = str(v).strip()
        return v if v else None

    @field_validator("allowed_content_types", mode="before")
    @classmethod
    def _parse_allowed_content_types(
        cls, v: Union[str, Set[str], List[str], None]
    ) -> Set[str]:
        if v is None:
            return {"image/jpeg", "image/png", "image/webp"}
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("[") and v.endswith("]"):
                try:
                    return set(json.loads(v))
                except Exception:
                    pass
            return {item.strip() for item in v.split(",") if item.strip()}
        return set(v)

    @field_validator("cors_allowed_origins", mode="before")
    @classmethod
    def _parse_cors_origins(
        cls, v: Union[str, List[str], None]
    ) -> List[str]:
        if v is None:
            return []
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("[") and v.endswith("]"):
                try:
                    return list(json.loads(v))
                except Exception:
                    pass
            return [item.strip() for item in v.split(",") if item.strip()]
        return list(v)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


# Singleton instance
settings = Settings()


def get_settings() -> Settings:
    """Return the global Settings singleton."""
    return settings
