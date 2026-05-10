#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import threading
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from minerva_kernel.daemon import create_server
from minerva_kernel.types import Observation


SCHEMA_VERSION = "minerva.minervad_smoke.v0"


def run_smoke() -> dict[str, Any]:
    server = create_server(host="127.0.0.1", port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        base_url = f"http://{host}:{port}"
        health = _get_json(f"{base_url}/health")
        diagnosis = _post_json(f"{base_url}/diagnose", _observation().to_dict())
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    checks = {
        "health_ok": health.get("status") == "ok",
        "diagnosis_schema": diagnosis.get("schema_version") == "minervad_diagnosis.v0",
        "policy_allowed": diagnosis.get("policy_decision", {}).get("allowed") is True,
        "not_executed": diagnosis.get("execution", {}).get("state") == "not_executed",
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "ready": all(checks.values()),
        "checks": checks,
        "health_schema_version": health.get("schema_version"),
        "diagnosis_action": diagnosis.get("decision", {}).get("action"),
        "execution_state": diagnosis.get("execution", {}).get("state"),
    }


def _get_json(url: str) -> dict[str, Any]:
    with urllib.request.urlopen(url, timeout=2) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("response must be a JSON object")
    return payload


def _post_json(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=2) as response:
        parsed = json.loads(response.read().decode("utf-8"))
    if not isinstance(parsed, dict):
        raise ValueError("response must be a JSON object")
    return parsed


def _observation() -> Observation:
    return Observation(
        command="python3 -m unittest discover -s tests",
        cwd="/workspace/minerva-ai-kernel",
        exit_code=1,
        stdout_tail="",
        stderr_tail="ModuleNotFoundError: No module named yaml",
        duration_ms=300,
        source="minervad_smoke",
        policy_summary="local smoke observation; no action execution",
    )


def main() -> int:
    try:
        payload = run_smoke()
    except Exception as exc:  # pragma: no cover - defensive script boundary
        print(f"minervad smoke failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True))
    return 0 if payload["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
