from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any

from minerva_kernel.policy import DANGEROUS_ACTION_LABELS, READ_ONLY_ACTIONS, validate_payload
from minerva_kernel.types import INSTRUCTION_SET_V0, RISK_LEVELS


ROOT = Path(__file__).resolve().parents[1]
TAXONOMY_PATH = ROOT / "taxonomies" / "aiops-v0.json"
REQUIRED_GROUPS = {"ci_cd", "config", "deployment", "network", "llm_runtime"}


class AiopsTaxonomyTests(unittest.TestCase):
    def test_taxonomy_covers_required_groups(self) -> None:
        taxonomy = _load_taxonomy()

        self.assertEqual(taxonomy["schema_version"], "minerva.aiops_taxonomy.v0")
        self.assertEqual(
            {group["id"] for group in taxonomy["groups"]},
            REQUIRED_GROUPS,
        )

    def test_failure_labels_are_unique_and_structured(self) -> None:
        labels: set[str] = set()

        for failure in _failures():
            with self.subTest(label=failure.get("label")):
                label = _required_string(failure, "label")
                self.assertNotIn(label, labels)
                labels.add(label)
                self.assertTrue(_required_string(failure, "definition"))
                self.assert_non_empty_strings(failure, "signals")
                self.assertIn(failure.get("risk"), RISK_LEVELS)
                self.assertIs(failure.get("writes_allowed"), False)
                self.assertIsInstance(failure.get("escalation_required"), bool)

    def test_safe_actions_map_to_minerva_instruction_set(self) -> None:
        for failure in _failures():
            action = _required_string(failure, "safe_action")
            with self.subTest(label=failure["label"], action=action):
                self.assertIn(action, INSTRUCTION_SET_V0)

    def test_non_escalation_actions_remain_allowed_by_default_policy(self) -> None:
        for failure in _failures():
            if failure["escalation_required"]:
                continue
            action = failure["safe_action"]
            with self.subTest(label=failure["label"], action=action):
                self.assertIn(action, READ_ONLY_ACTIONS)
                decision = validate_payload({"action": action})
                self.assertTrue(decision.allowed, decision.reason)

    def test_escalation_actions_are_policy_blocked_by_default(self) -> None:
        for failure in _failures():
            if not failure["escalation_required"]:
                continue
            action = failure["safe_action"]
            with self.subTest(label=failure["label"], action=action):
                decision = validate_payload({"action": action})
                self.assertFalse(decision.allowed)

    def test_prohibited_action_labels_match_policy_blocks(self) -> None:
        taxonomy = _load_taxonomy()
        prohibited = taxonomy["safe_action_contract"]["prohibited_action_labels"]

        self.assertTrue(set(DANGEROUS_ACTION_LABELS) & set(prohibited))
        for action in prohibited:
            with self.subTest(action=action):
                decision = validate_payload({"action": action})
                self.assertFalse(decision.allowed)

    def assert_non_empty_strings(self, payload: dict[str, Any], field: str) -> None:
        value = payload.get(field)
        self.assertIsInstance(value, list)
        self.assertTrue(value)
        self.assertTrue(all(isinstance(item, str) and item for item in value))


def _load_taxonomy() -> dict[str, Any]:
    with TAXONOMY_PATH.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise AssertionError("taxonomy must be a JSON object")
    return payload


def _failures() -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    for group in _load_taxonomy()["groups"]:
        group_failures = group.get("failures")
        if not isinstance(group_failures, list) or not group_failures:
            raise AssertionError(f"group must include failures: {group.get('id')}")
        for failure in group_failures:
            if not isinstance(failure, dict):
                raise AssertionError("failure entry must be an object")
            failures.append(failure)
    return failures


def _required_string(payload: dict[str, Any], field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value:
        raise AssertionError(f"{field} must be a non-empty string")
    return value


if __name__ == "__main__":
    unittest.main()
