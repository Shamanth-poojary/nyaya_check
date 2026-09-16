"""
tests/test_integration_phase5.py — Verification suite for Phase 05 Service Integration features.

Covers:
  - API Key Authentication (enabled vs disabled, missing, invalid, valid, health bypass)
  - CORS Middleware (allowed origins vs disallowed origins, preflight OPTIONS)
  - Health & Readiness endpoints (/v1/health, /v1/ready)
  - Configuration Settings (environment parsing, validation, limits)
  - API Versioning (/v1 prefix contract)
"""

import io
from fastapi.testclient import TestClient
from PIL import Image

from app.config import Settings, settings
from app.main import app

client = TestClient(app)


def _sample_image_bytes(width: int = 100, height: int = 80) -> io.BytesIO:
    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


class TestAuthentication:
    """Test API Key authentication behavior on versioned endpoints."""

    def test_auth_disabled_by_default(self):
        """When settings.api_key is None, requests without key succeed."""
        settings.api_key = None
        buf = _sample_image_bytes()
        resp = client.post("/v1/extract", files={"image": ("sample.png", buf, "image/png")})
        assert resp.status_code == 200

    def test_auth_enforced_when_configured_missing_key(self):
        """When API_KEY is set, request without X-API-Key header returns 401."""
        settings.api_key = "test-secret-key-123"
        try:
            buf = _sample_image_bytes()
            resp = client.post("/v1/extract", files={"image": ("sample.png", buf, "image/png")})
            assert resp.status_code == 401
            assert "Invalid or missing API key" in resp.json()["detail"]
        finally:
            settings.api_key = None

    def test_auth_enforced_wrong_key(self):
        """When API_KEY is set, request with wrong X-API-Key returns 401."""
        settings.api_key = "test-secret-key-123"
        try:
            buf = _sample_image_bytes()
            resp = client.post(
                "/v1/extract",
                headers={"X-API-Key": "wrong-key"},
                files={"image": ("sample.png", buf, "image/png")},
            )
            assert resp.status_code == 401
            assert "Invalid or missing API key" in resp.json()["detail"]
        finally:
            settings.api_key = None

    def test_auth_enforced_valid_key(self):
        """When API_KEY is set, request with correct X-API-Key succeeds."""
        settings.api_key = "test-secret-key-123"
        try:
            buf = _sample_image_bytes()
            resp = client.post(
                "/v1/extract",
                headers={"X-API-Key": "test-secret-key-123"},
                files={"image": ("sample.png", buf, "image/png")},
            )
            assert resp.status_code == 200
        finally:
            settings.api_key = None

    def test_health_and_ready_bypass_auth(self):
        """Health and readiness checks MUST succeed without an API key even when auth is active."""
        settings.api_key = "test-secret-key-123"
        try:
            resp_health = client.get("/v1/health")
            assert resp_health.status_code == 200
            assert resp_health.json() == {"status": "ok"}

            resp_ready = client.get("/v1/ready")
            assert resp_ready.status_code == 200
            assert resp_ready.json()["engine"] == "paddleocr"
        finally:
            settings.api_key = None


class TestCORSMiddleware:
    """Test CORS headers for permitted and non-permitted frontend origins."""

    def test_allowed_origin_receives_cors_header(self):
        origin = "http://localhost:3000"
        resp = client.get(
            "/v1/health",
            headers={"Origin": origin},
        )
        assert resp.status_code == 200
        assert resp.headers.get("access-control-allow-origin") == origin
        assert resp.headers.get("access-control-allow-credentials") == "true"

    def test_disallowed_origin_does_not_receive_cors_header(self):
        resp = client.get(
            "/v1/health",
            headers={"Origin": "http://malicious-external-site.com"},
        )
        assert resp.status_code == 200
        # In CORS specification, disallowed origins are not echoed in Access-Control-Allow-Origin
        assert "access-control-allow-origin" not in resp.headers

    def test_preflight_options_request_allowed_origin(self):
        origin = "http://localhost:5173"
        resp = client.options(
            "/v1/check",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "X-API-Key,Content-Type",
            },
        )
        assert resp.status_code == 200
        assert resp.headers.get("access-control-allow-origin") == origin
        assert "POST" in resp.headers.get("access-control-allow-methods", "")


class TestReadinessAndHealth:
    """Test health liveness and model readiness reporting."""

    def test_health_liveness(self):
        resp = client.get("/v1/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_ready_endpoint_structure(self):
        resp = client.get("/v1/ready")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("ready", "initializing")
        assert data["engine"] == "paddleocr"
        assert isinstance(data["modelLoaded"], bool)


class TestConfigSettings:
    """Test Settings model validation and environment parsing."""

    def test_settings_defaults(self):
        cfg = Settings()
        assert cfg.max_images_per_request == 10
        assert cfg.max_file_size_mb == 15
        assert "image/jpeg" in cfg.allowed_content_types
        assert cfg.preprocess_enabled_default is False
        assert cfg.log_level in ("INFO", "DEBUG", "WARNING")

    def test_settings_comma_separated_origins_parsing(self):
        cfg = Settings(cors_allowed_origins="http://site-a.com, http://site-b.com")
        assert "http://site-a.com" in cfg.cors_allowed_origins
        assert "http://site-b.com" in cfg.cors_allowed_origins

    def test_settings_json_array_origins_parsing(self):
        cfg = Settings(cors_allowed_origins='["http://app.local:3000"]')
        assert cfg.cors_allowed_origins == ["http://app.local:3000"]

    def test_empty_string_api_key_treated_as_none(self):
        cfg = Settings(api_key="   ")
        assert cfg.api_key is None


class TestTimingInstrumentation:
    """Test X-Process-Time header added by middleware."""

    def test_process_time_header_present(self):
        resp = client.get("/v1/health")
        assert resp.status_code == 200
        assert "x-process-time" in resp.headers
        assert resp.headers["x-process-time"].endswith("s")
