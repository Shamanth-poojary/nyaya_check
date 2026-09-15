# app/rules/__init__.py
# Phase 03: Rules Engine package.
# Public API: evaluate(response) -> ComplianceResult
from app.rules.engine import evaluate  # noqa: F401

__all__ = ["evaluate"]
