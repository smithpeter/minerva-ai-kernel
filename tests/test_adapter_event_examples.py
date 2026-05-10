from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any

from minerva_kernel.policy import validate_action
from minerva_kernel.types import Decision, Observation


ROOT = Path(__file__).resolve().parents[1]
EVENT_DIR = ROOT / "examples" / "adapter-events"
REQUIRED_PLATFORM_TYPES = {"ci", "aiops"}


class AdapterEventExampleTests(unittest.TestCase):
    def test_examples_cover_ci_and_aiops_events(self) -> None:
        payloads = _load_events()

        self.assertEqual(
            {payload["platform"]["type"] for payload in payloads},
            REQUIRED_PLATFORM_TYPES,
        )

    def test_examples_embed_valid_observation_and_decision_contracts(self) -> None:
        for payload in _load_events():
            with self.subTest(event=payload["event"]["id"]):
                observation = Observation.from_dict(payload["observation"])
                decision = Decision.from_dict(payload["diagnosis"]["decision"])

                self.assertEqual(observation.source.split(".")[0], "adapter")
                self.assertTrue(observation.policy_summary)
                self.assertTrue(decision.evidence)

    def test_examples_match_policy_runtime_result(self) -> None:
        for payload in _load_events():
            with self.subTest(event=payload["event"]["id"]):
                decision = Decision.from_dict(payload["diagnosis"]["decision"])
                expected = payload["diagnosis"]["policy_decision"]
                actual = validate_action(decision)

                self.assertEqual(expected["allowed"], actual.allowed)
                self.assertEqual(expected["reason"], actual.reason)

    def test_examples_are_report_only_and_do_not_override_host_status(self) -> None:
        for payload in _load_events():
            with self.subTest(event=payload["event"]["id"]):
                reporting = payload["reporting"]
                execution = payload["diagnosis"]["execution"]

                self.assertIs(reporting["policy_is_authorization"], True)
                self.assertIs(reporting["adapter_executes_actions"], False)
                self.assertIs(reporting["host_status_override"], False)
                self.assertEqual(execution["state"], "not_executed")

    def test_ci_example_keeps_secret_redacted(self) -> None:
        payload = _event_by_platform("ci")
        text = json.dumps(payload, sort_keys=True)

        self.assertIn("[REDACTED:API_KEY]", text)
        self.assertNotIn("sk-", text)
        self.assertNotIn("BEGIN PRIVATE KEY", text)
        self.assertEqual(payload["observation"]["redactions"]["count"], 1)


def _load_events() -> list[dict[str, Any]]:
    paths = sorted(EVENT_DIR.glob("*.adapter-event.json"))
    if not paths:
        raise AssertionError(f"no adapter event examples found in {EVENT_DIR}")

    payloads: list[dict[str, Any]] = []
    for path in paths:
        with path.open(encoding="utf-8") as handle:
            payload = json.load(handle)
        if not isinstance(payload, dict):
            raise AssertionError(f"event must be a JSON object: {path}")
        if payload.get("schema_version") != "minerva.adapter_event.v0":
            raise AssertionError(f"bad adapter event schema: {path}")
        _required_object(payload, "producer")
        _required_object(payload, "platform")
        _required_object(payload, "event")
        _required_object(payload, "observation")
        _required_object(payload, "diagnosis")
        _required_object(payload, "reporting")
        payloads.append(payload)
    return payloads


def _event_by_platform(platform_type: str) -> dict[str, Any]:
    for payload in _load_events():
        if payload["platform"]["type"] == platform_type:
            return payload
    raise AssertionError(f"missing platform type: {platform_type}")


def _required_object(payload: dict[str, Any], field: str) -> dict[str, Any]:
    value = payload.get(field)
    if not isinstance(value, dict):
        raise AssertionError(f"{field} must be an object")
    return value


if __name__ == "__main__":
    unittest.main()
