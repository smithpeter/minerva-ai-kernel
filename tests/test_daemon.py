from __future__ import annotations

import json
import threading
import unittest
import urllib.error
import urllib.request

from minerva_kernel.daemon import create_server, health_payload


class DaemonTests(unittest.TestCase):
    def test_health_payload_contract(self) -> None:
        payload = health_payload()

        self.assertEqual(payload["schema_version"], "minervad_health.v0")
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["service"], "minervad")
        self.assertEqual(payload["mode"], "prototype")

    def test_health_endpoint_serves_json_on_local_random_port(self) -> None:
        server = self._create_local_server_or_skip()
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

    def test_unknown_endpoint_returns_404_json(self) -> None:
        server = self._create_local_server_or_skip()
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

    def _create_local_server_or_skip(self):
        try:
            return create_server(host="127.0.0.1", port=0)
        except PermissionError as exc:
            self.skipTest(f"local socket bind unavailable: {exc}")


if __name__ == "__main__":
    unittest.main()
