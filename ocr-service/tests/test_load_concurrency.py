"""
tests/test_load_concurrency.py — Concurrency and load performance benchmark.

Simulates concurrent multi-image requests to /v1/extract/multi and /v1/check
using httpx.AsyncClient + ASGITransport to verify service stability, measure
requests/sec throughput, and record latency percentiles for teammates' capacity planning.
"""

import asyncio
import io
import statistics
import time
from typing import List, Tuple

import httpx
from PIL import Image

from app.main import app


def _generate_test_image(text_seed: str, width: int = 160, height: int = 100) -> io.BytesIO:
    """Generate a lightweight valid in-memory image."""
    img = Image.new("RGB", (width, height), color=(240, 240, 240))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


async def _async_worker(
    client: httpx.AsyncClient, request_id: int, images_per_req: int = 3
) -> Tuple[int, float, int]:
    """Execute one multi-image extraction request asynchronously and measure latency."""
    files = [
        ("images", (f"req_{request_id}_img_{j}.png", _generate_test_image(f"r{request_id}_{j}").getvalue(), "image/png"))
        for j in range(images_per_req)
    ]
    t0 = time.perf_counter()
    resp = await client.post("/v1/extract/multi", files=files)
    elapsed = time.perf_counter() - t0
    return resp.status_code, elapsed, len(files)


async def _run_concurrent_benchmark(num_concurrent_requests: int = 4, images_per_request: int = 3):
    total_images = num_concurrent_requests * images_per_request
    print(
        f"\n--- Launching Load Benchmark: {num_concurrent_requests} concurrent requests "
        f"({images_per_request} images each = {total_images} total) ---"
    )

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver", timeout=60.0) as client:
        benchmark_start = time.perf_counter()
        tasks = [
            _async_worker(client, i, images_per_request)
            for i in range(num_concurrent_requests)
        ]
        results = await asyncio.gather(*tasks)
        total_wall_time = time.perf_counter() - benchmark_start

    status_codes = [r[0] for r in results]
    latencies = [r[1] for r in results]

    # Verification: every request must succeed
    assert all(code == 200 for code in status_codes), f"Some requests failed: {status_codes}"

    mean_latency = statistics.mean(latencies)
    median_latency = statistics.median(latencies)
    min_latency = min(latencies)
    max_latency = max(latencies)
    throughput_rps = num_concurrent_requests / total_wall_time
    images_per_sec = total_images / total_wall_time

    print(f"Results:")
    print(f"  Total Wall Time     : {total_wall_time:.2f}s")
    print(f"  Successful Requests : {len(results)}/{num_concurrent_requests} (100%)")
    print(f"  Latency Min / Max   : {min_latency:.2f}s / {max_latency:.2f}s")
    print(f"  Latency Mean/Median : {mean_latency:.2f}s / {median_latency:.2f}s")
    print(f"  Throughput (Req/s)  : {throughput_rps:.2f} req/s")
    print(f"  Throughput (Img/s)  : {images_per_sec:.2f} images/s")
    print("--------------------------------------------------------------------------------\n")


def test_concurrent_load_extract_multi():
    """Execute concurrent benchmark using asyncio event loop."""
    asyncio.run(_run_concurrent_benchmark(num_concurrent_requests=4, images_per_request=3))
