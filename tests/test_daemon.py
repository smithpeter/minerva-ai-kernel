from __future__ import annotations

import json
import threading
import unittest
import urllib.error
import urllib.request

from minerva_kernel import Observation
from minerva_kernel.daemon import create_server, health_payload


class DaemonTests(unittest.TestCase):
    def test_health_payload_contract(self) -> None:
        payload = health_payload()

        self.assertEqual(payload["schema_version"], "minervad_health.v0")
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["service"], "minervad")
        self.assertEqual(payload["mode"], "prototype")

    def test_health_endpoint_serves_json_on_local_random_port(self) -> None:
        server = create_server(host="127.0.0.1", port=0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            host, port = server.server_address
            with urllib.request.urlopen(
                f"http://{host}:{port}/health",
                timeout=2,
            ) as response:
                body = response.read().decode("utf-8")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

        payload = json.loads(body)
        self.assertEqual(payload["schema_version"], "minervad_health.v0")
        self.assertEqual(payload["status"], "ok")

    def test_diagnose_endpoint_returns_policy_gated_decision(self) -> None:
        with _running_server() as base_url:
            payload = _post_json(f"{base_url}/diagnose", _observation().to_dict())

        self.assertEqual(payload["schema_version"], "minervad_diagnosis.v0")
        self.assertEqual(payload["decision"]["schema_version"], "decision.v0")
        self.assertEqual(payload["decision"]["failure"], "missing_dependency")
        self.assertEqual(payload["decision"]["action"], "inspect_dependencies")
        self.assertTrue(payload["policy_decision"]["allowed"])
        self.assertEqual(payload["execution"]["state"], "not_executed")

    def test_diagnose_endpoint_returns_policy_blocked_decision(self) -> None:
        observation = Observation(
            command="python3 run.py",
            cwd="/workspace/example-project",
            exit_code=1,
            stdout_tail="",
            stderr_tail="process ended without concrete diagnostic output",
            duration_ms=100,
            source="daemon_test",
            policy_summary="ambiguous failure should stay policy gated",
        )

        with _running_server() as base_url:
            payload = _post_json(f"{base_url}/diagnose", observation.to_dict())

        self.assertEqual(payload["decision"]["failure"], "unknown_failure")
        self.assertFalse(payload["policy_decision"]["allowed"])
        self.assertEqual(
            payload["policy_decision"]["reason"],
            "confidence below threshold",
        )
        self.assertEqual(payload["execution"]["state"], "not_executed")

    def test_diagnose_endpoint_rejects_invalid_json(self) -> None:
        with _running_server() as base_url:
            request = urllib.request.Request(
                f"{base_url}/diagnose",
                data=b"{",
                method="POST",
                headers={"Content-Type": "application/json"},
            )
            with self.assertRaises(urllib.error.HTTPError) as raised:
                urllib.request.urlopen(request, timeout=2)

        payload = json.loads(raised.exception.read().decode("utf-8"))
        self.assertEqual(raised.exception.code, 400)
        self.assertEqual(payload["error"], "invalid_json")

    def test_diagnose_endpoint_rejects_invalid_schema(self) -> None:
        with _running_server() as base_url:
            with self.assertRaises(urllib.error.HTTPError) as raised:
                _post_json(
                    f"{base_url}/diagnose",
                    {"schema_version": "wrong.v0"},
                )

        payload = json.loads(raised.exception.read().decode("utf-8"))
        self.assertEqual(raised.exception.code, 400)
        self.assertEqual(payload["error"], "invalid_observation")

    def test_diagnose_endpoint_rejects_wrong_method(self) -> None:
        with _running_server() as base_url:
            with self.assertRaises(urllib.error.HTTPError) as raised:
                urllib.request.urlopen(f"{base_url}/diagnose", timeout=2)

        payload = json.loads(raised.exception.read().decode("utf-8"))
        self.assertEqual(raised.exception.code, 405)
        self.assertEqual(payload["error"], "method_not_allowed")

    def test_diagnose_endpoint_rejects_oversized_body(self) -> None:
        with _running_server() as base_url:
            request = urllib.request.Request(
                f"{base_url}/diagnose",
                data=b"{}",
                method="POST",
                headers={
                    "Content-Type": "application/json",
                    "Content-Length": "1000001",
                },
            )
            with self.assertRaises(urllib.error.HTTPError) as raised:
                urllib.request.urlopen(request, timeout=2)

        payload = json.loads(raised.exception.read().decode("utf-8"))
        self.assertEqual(raised.exception.code, 413)
        self.assertEqual(payload["error"], "request_too_large")

    def test_unknown_endpoint_returns_404_json(self) -> None:
        server = create_server(host="127.0.0.1", port=0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            host, port = server.server_address
            with self.assertRaises(urllib.error.HTTPError) as raised:
                urllib.request.urlopen(f"http://{host}:{port}/missing", timeout=2)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

        self.assertEqual(raised.exception.code, 404)


class _running_server:
    def __enter__(self) -> str:
        self.server = create_server(host="127.0.0.1", port=0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        host, port = self.server.server_address
        return f"http://{host}:{port}"

    def __exit__(self, *exc_info: object) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)


def _post_json(url: str, payload: dict[str, object]) -> dict[str, object]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=2) as response:
        body = response.read().decode("utf-8")
    parsed = json.loads(body)
    if not isinstance(parsed, dict):
        raise AssertionError("response must be a JSON object")
    return parsed


def _observation() -> Observation:
    return Observation(
        command="python3 -m unittest discover -s tests",
        cwd="/workspace/example-project",
        exit_code=1,
        stdout_tail="",
        stderr_tail="ModuleNotFoundError: No module named 'example_package'",
        duration_ms=742,
        source="daemon_test",
        policy_summary="test observation with bounded stderr and no credentials",
    )


if __name__ == "__main__":
    unittest.main()
