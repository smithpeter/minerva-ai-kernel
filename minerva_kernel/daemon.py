from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from .sdk import Diagnosis, diagnose_observation
from .types import Observation


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
MAX_DIAGNOSE_BODY_BYTES = 1_000_000


def health_payload() -> dict[str, Any]:
    return {
        "schema_version": "minervad_health.v0",
        "status": "ok",
        "service": "minervad",
        "mode": "prototype",
    }


def diagnosis_payload(diagnosis: Diagnosis) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": "minervad_diagnosis.v0",
        "decision": diagnosis.decision.to_dict(),
        "policy_decision": {
            "allowed": diagnosis.policy_decision.allowed,
            "reason": diagnosis.policy_decision.reason,
        },
        "execution": {
            "state": "not_executed",
            "reason": "minervad diagnose is read-only",
        },
    }
    if diagnosis.redactions and diagnosis.redactions.count:
        payload["redactions"] = diagnosis.redactions.to_dict()
    return payload


def create_server(
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), _Handler)


def serve(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> None:
    server = create_server(host=host, port=port)
    try:
        server.serve_forever()
    finally:
        server.server_close()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="python -m minerva_kernel.daemon",
        description="Run the local-only minervad prototype health server.",
    )
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args(argv)
    serve(host=args.host, port=args.port)


class _Handler(BaseHTTPRequestHandler):
    server_version = "minervad/0"

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
        if self.path == "/diagnose":
            self._write_json(405, {"error": "method_not_allowed"})
            return
        if self.path != "/health":
            self._write_json(404, {"error": "not_found"})
            return
        self._write_json(200, health_payload())

    def do_POST(self) -> None:  # noqa: N802 - stdlib handler API
        if self.path != "/diagnose":
            self._write_json(404, {"error": "not_found"})
            return

        body = self._read_bounded_body()
        if body is None:
            return

        try:
            payload = json.loads(body.decode("utf-8"))
        except UnicodeDecodeError as exc:
            self._write_json(400, {"error": "invalid_json", "detail": str(exc)})
            return
        except json.JSONDecodeError as exc:
            self._write_json(400, {"error": "invalid_json", "detail": exc.msg})
            return

        if not isinstance(payload, dict):
            self._write_json(
                400,
                {"error": "invalid_observation", "detail": "request body must be an object"},
            )
            return

        try:
            observation = Observation.from_dict(payload)
            diagnosis = diagnose_observation(observation)
        except ValueError as exc:
            self._write_json(400, {"error": "invalid_observation", "detail": str(exc)})
            return

        self._write_json(200, diagnosis_payload(diagnosis))

    def log_message(self, format: str, *args: object) -> None:
        return

    def _read_bounded_body(self) -> bytes | None:
        raw_length = self.headers.get("Content-Length")
        if raw_length is None:
            self._write_json(
                400,
                {"error": "invalid_request", "detail": "Content-Length is required"},
            )
            return None

        try:
            length = int(raw_length)
        except ValueError:
            self._write_json(
                400,
                {"error": "invalid_request", "detail": "Content-Length must be an integer"},
            )
            return None

        if length <= 0:
            self._write_json(
                400,
                {"error": "invalid_request", "detail": "request body is required"},
            )
            return None
        if length > MAX_DIAGNOSE_BODY_BYTES:
            self._write_json(
                413,
                {
                    "error": "request_too_large",
                    "detail": f"body exceeds {MAX_DIAGNOSE_BODY_BYTES} bytes",
                },
            )
            return None

        return self.rfile.read(length)

    def _write_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=True, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    main()
