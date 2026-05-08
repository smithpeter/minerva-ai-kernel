from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_DIR = ROOT / "examples" / "pack-manifests"
EXPECTED_PACK_TYPES = {"taxonomy", "policy", "model", "adapter"}
REQUIRED_TOP_LEVEL_FIELDS = {
    "schema_version",
    "pack_type",
    "id",
    "name",
    "version",
    "description",
    "license",
    "ownership",
    "compatibility",
    "safety",
}
REQUIRED_SAFETY_VALUES = {
    "redaction_required": True,
    "policy_gated_decisions": True,
    "no_auto_repair_by_default": True,
    "cpu_local_minimum_path_preserved": True,
    "remote_services_required": False,
    "secrets_allowed": False,
}
REQUIRED_TYPE_FIELDS = {
    "taxonomy": {"domain", "failure_labels", "safe_action_labels", "negative_examples"},
    "policy": {"mode", "default_decision", "allow", "deny", "human_approval_required"},
    "model": {
        "model_name",
        "source",
        "weights_included",
        "expected_hardware",
        "prompt_contract",
        "eval_report",
    },
    "adapter": {
        "target_system",
        "dependencies",
        "observation_mapping",
        "redaction_boundary",
        "decision_consumption",
        "failure_behavior",
    },
}


class PackManifestExampleTests(unittest.TestCase):
    def test_manifest_examples_cover_each_pack_type(self) -> None:
        manifests = _load_manifests()

        self.assertEqual(
            {payload["pack_type"] for _, payload in manifests},
            EXPECTED_PACK_TYPES,
        )

    def test_manifest_examples_have_required_common_fields(self) -> None:
        for path, payload in _load_manifests():
            with self.subTest(manifest=path.name):
                self.assertEqual(payload["schema_version"], "minerva.pack_manifest.v0")
                self.assertLessEqual(REQUIRED_TOP_LEVEL_FIELDS, set(payload))
                self.assertTrue(payload["id"].startswith("minerva.examples."))

                ownership = _required_object(payload, "ownership")
                self.assertIsInstance(ownership.get("owner"), str)
                self.assertTrue(ownership.get("owner"))
                self.assert_non_empty_list(ownership, "maintainers")
                self.assert_non_empty_list(ownership, "reviewers")
                self.assertIn("contact", ownership["maintainers"][0])

                compatibility = _required_object(payload, "compatibility")
                minerva = _required_object(compatibility, "minerva")
                self.assertIsInstance(minerva.get("min_version"), str)
                self.assertIsInstance(minerva.get("max_tested_version"), str)
                schemas = _required_object(compatibility, "schemas")
                self.assertEqual(schemas.get("pack_manifest"), "minerva.pack_manifest.v0")
                self.assertTrue({"observation", "decision"} & set(schemas))

                safety = _required_object(payload, "safety")
                for field, expected_value in REQUIRED_SAFETY_VALUES.items():
                    self.assertEqual(safety.get(field), expected_value)
                self.assert_non_empty_list(safety, "risk_notes")

    def test_manifest_examples_have_type_specific_fields(self) -> None:
        for path, payload in _load_manifests():
            pack_type = payload["pack_type"]
            with self.subTest(manifest=path.name):
                self.assertIn(pack_type, EXPECTED_PACK_TYPES)
                type_payload = _required_object(payload, pack_type)
                self.assertLessEqual(REQUIRED_TYPE_FIELDS[pack_type], set(type_payload))

    def test_policy_example_fails_closed(self) -> None:
        policy = _manifest_by_type("policy")["policy"]

        self.assertEqual(policy["default_decision"], "deny")
        self.assertTrue(policy["deny"])
        self.assertIn("filesystem_write", policy["human_approval_required"])
        self.assertTrue(policy["audit"]["blocked_reason_required"])

    def test_model_example_requires_structured_eval_safety(self) -> None:
        model = _manifest_by_type("model")["model"]
        eval_report = model["eval_report"]
        prompt_contract = model["prompt_contract"]

        self.assertEqual(prompt_contract["output_schema"], "decision.v0")
        self.assertEqual(eval_report["dangerous_action_rate_max"], 0.0)
        self.assertTrue(eval_report["redaction_coverage_reported"])

    def assert_non_empty_list(self, payload: dict[str, Any], field: str) -> None:
        value = payload.get(field)
        self.assertIsInstance(value, list)
        self.assertTrue(value)


def _manifest_by_type(pack_type: str) -> dict[str, Any]:
    for _, payload in _load_manifests():
        if payload["pack_type"] == pack_type:
            return payload
    raise AssertionError(f"missing manifest for pack type: {pack_type}")


def _load_manifests() -> list[tuple[Path, dict[str, Any]]]:
    paths = sorted(MANIFEST_DIR.glob("*.manifest.json"))
    if not paths:
        raise AssertionError(f"no manifest examples found in {MANIFEST_DIR}")

    manifests: list[tuple[Path, dict[str, Any]]] = []
    for path in paths:
        with path.open(encoding="utf-8") as handle:
            payload = json.load(handle)
        if not isinstance(payload, dict):
            raise AssertionError(f"manifest must be a JSON object: {path}")
        manifests.append((path, payload))
    return manifests


def _required_object(payload: dict[str, Any], field: str) -> dict[str, Any]:
    value = payload.get(field)
    if not isinstance(value, dict):
        raise AssertionError(f"{field} must be an object")
    return value


if __name__ == "__main__":
    unittest.main()
