"""Performance gate: fails the build if p95 latency of POST /quote exceeds a threshold.

The threshold is read from PERF_P95_MS (default 50). Raise it deliberately
in CI config if the runner class changes; do not raise it to make a
regression pass.
"""

import json
import os
import statistics
import threading
import time
import urllib.request

import pytest

from quote_service.http_app import make_server

P95_THRESHOLD_MS = float(os.environ.get("PERF_P95_MS", "50"))
SAMPLES = 200
WARMUP = 20


@pytest.fixture(scope="module")
def base_url():
    server = make_server(port=0)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    host, port = server.server_address
    yield f"http://{host}:{port}"
    server.shutdown()
    server.server_close()


def test_quote_p95_latency_under_threshold(base_url):
    payload = json.dumps({
        "items": [{"sku": f"SKU-{i}", "unit_price": 9.99, "qty": 3} for i in range(10)],
        "discount_pct": 5,
    }).encode()

    def one_call():
        req = urllib.request.Request(
            base_url + "/quote", data=payload, method="POST",
            headers={"Content-Type": "application/json"},
        )
        start = time.perf_counter()
        with urllib.request.urlopen(req, timeout=5) as resp:
            resp.read()
        return (time.perf_counter() - start) * 1000

    for _ in range(WARMUP):
        one_call()
    samples = sorted(one_call() for _ in range(SAMPLES))

    p95 = samples[int(0.95 * len(samples)) - 1]
    median = statistics.median(samples)
    print(f"\nlatency ms: median={median:.2f} p95={p95:.2f} threshold={P95_THRESHOLD_MS}")
    assert p95 < P95_THRESHOLD_MS, (
        f"p95 {p95:.2f}ms exceeds threshold {P95_THRESHOLD_MS}ms"
    )
