import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

FEATURE_X = os.getenv("ENABLE_FEATURE_X") == "true"
VERSION = os.getenv("APP_VERSION", "")

ready = threading.Event()


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/ping":
            self._reply(200, self._pong())
        elif self.path == "/ready":
            if ready.is_set():
                self._reply(200, "ready")
            else:
                self._reply(503, "starting")
        elif self.path == "/feature" and FEATURE_X:
            self._reply(200, "Feature X is enabled!")
        else:
            self._reply(404, "not found")

    def _pong(self) -> str:
        text = f"pong {VERSION}" if VERSION else "pong"
        if FEATURE_X and self.headers.get("X-Feature-Enabled", "").lower() == "true":
            text += ", feature X"
        return text

    def _reply(self, status: int, body: str) -> None:
        payload = (body + "\n").encode()
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format, *args):
        pass


def start_http_server(port: int) -> None:
    server = ThreadingHTTPServer(("", port), _Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
