import io

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app

client = TestClient(app)


def _sample_image_bytes(width: int = 120, height: int = 80) -> io.BytesIO:
    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_extract_valid_image_returns_placeholder_schema():
    buf = _sample_image_bytes(120, 80)
    resp = client.post("/extract", files={"image": ("sample.png", buf, "image/png")})
    assert resp.status_code == 200

    data = resp.json()
    assert data["document"]["width"] == 120
    assert data["document"]["height"] == 80
    assert data["commodity"]["found"] is False
    assert data["mrp"]["found"] is False
    assert data["rawOCR"] == []


def test_extract_rejects_non_image():
    resp = client.post(
        "/extract",
        files={"image": ("notes.txt", io.BytesIO(b"hello"), "text/plain")},
    )
    assert resp.status_code == 400


def test_extract_requires_file():
    resp = client.post("/extract")
    assert resp.status_code == 422
