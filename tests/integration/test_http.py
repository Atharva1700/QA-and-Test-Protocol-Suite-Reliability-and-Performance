"""Integration tests: real HTTP server on a random port, real sockets."""

import json
import threading
import urllib.error
import urllib.request

import pytest

from quote_service.http_app import make_server


@pytest.fixture(scope="module")
def base_url():
    server = make_server(port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    yield f"http://{host}:{port}"
    server.shutdown()
    server.server_close()


def post(base_url, path, body, *, raw=None):
    data = raw if raw is not None else json.dumps(body).encode()
    req = urllib.request.Request(
        base_url + path, data=data, method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as err:
        return err.code, json.loads(err.read())


def test_valid_quote_returns_200_and_totals(base_url):
    status, body = post(base_url, "/quote", {
        "items": [{"sku": "A", "unit_price": 10.0, "qty": 2}],
        "discount_pct": 10,
    })
    assert status == 200
    assert float(body["total"]) == pytest.approx(18.0)


def test_unknown_path_returns_404(base_url):
    status, body = post(base_url, "/nope", {"items": []})
    assert status == 404


def test_invalid_json_returns_400(base_url):
    status, body = post(base_url, "/quote", None, raw=b"{not json")
    assert status == 400
    assert "JSON" in body["error"]


def test_non_object_body_returns_400(base_url):
    status, _ = post(base_url, "/quote", [1, 2, 3])
    assert status == 400


def test_domain_error_returns_400_with_message(base_url):
    status, body = post(base_url, "/quote", {"items": []})
    assert status == 400
    assert "non-empty" in body["error"]


def test_oversized_body_returns_413(base_url):
    status, _ = post(base_url, "/quote", None, raw=b"x" * (64 * 1024 + 1))
    assert status == 413
