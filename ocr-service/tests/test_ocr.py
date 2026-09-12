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


def test_extract_multi_accepts_multiple_images():
    buf1 = _sample_image_bytes(100, 80)
    buf2 = _sample_image_bytes(150, 90)
    resp = client.post(
        "/extract/multi",
        files=[
            ("images", ("photo1.png", buf1, "image/png")),
            ("images", ("photo2.png", buf2, "image/png")),
        ],
    )
    assert resp.status_code == 200
    data = resp.json()
    # Merged response uses the same shape as single-image /extract
    assert "mrp" in data and "manufacturer" in data
    # Two photos submitted -> two source documents tracked
    assert len(data["sourceDocuments"]) == 2
    image_ids = {d["imageId"] for d in data["sourceDocuments"]}
    assert image_ids == {"photo1.png", "photo2.png"}


def test_extract_multi_rejects_too_many_images():
    files = [("images", (f"p{i}.png", _sample_image_bytes(50, 50), "image/png")) for i in range(11)]
    resp = client.post("/extract/multi", files=files)
    assert resp.status_code == 400


def test_extract_multi_single_image_still_works():
    """A single image through the multi endpoint should behave sensibly
    (not crash on the 'only one result' edge case in the merge logic)."""
    buf = _sample_image_bytes(100, 100)
    resp = client.post(
        "/extract/multi", files=[("images", ("solo.png", buf, "image/png"))]
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["document"]["imageId"] == "solo.png"
    assert len(data["sourceDocuments"]) == 1
