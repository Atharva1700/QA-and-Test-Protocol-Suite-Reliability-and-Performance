"""Minimal HTTP wrapper: POST /quote with a JSON body. Standard library only."""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from quote_service.quote import QuoteError, quote

MAX_BODY_BYTES = 64 * 1024


class QuoteHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/quote":
            return self._send(404, {"error": "not found"})

        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            return self._send(400, {"error": "invalid Content-Length"})
        if length <= 0:
            return self._send(400, {"error": "request body required"})
        if length > MAX_BODY_BYTES:
            return self._send(413, {"error": "request body too large"})

        try:
            body = json.loads(self.rfile.read(length))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return self._send(400, {"error": "body must be valid JSON"})
        if not isinstance(body, dict):
            return self._send(400, {"error": "body must be a JSON object"})

        try:
            result = quote(body.get("items"), body.get("discount_pct", 0))
        except QuoteError as exc:
            return self._send(400, {"error": str(exc)})
        return self._send(200, result)

    def _send(self, status, payload):
        data = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format, *args):  # keep test output quiet
        pass


def make_server(host="127.0.0.1", port=0):
    return ThreadingHTTPServer((host, port), QuoteHandler)
