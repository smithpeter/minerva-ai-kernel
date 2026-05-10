from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "models" / "cpu_model_candidates.json"
ARTIFACT_EXAMPLE_PATH = ROOT / "evals" / "cpu_model_report_artifact.example.json"


class CPUModelCandidateRegistryTests(unittest.TestCase):
    def test_registry_loads_and_declares_contract(self) -> None:
        registry = _load_registry()

        self.assertEqual(
            registry["schema_version"],
            "minerva.cpu_model_candidate_registry.v0",
        )
        self.assertEqual(
            registry["scoring_contract"],
            "docs/cpu-model-eval-scoring-contract.md",
        )
        constraints = registry["selection_constraints"]
        self.assertEqual(constraints["maximum_parameters_millions"], 500)
        self.assertFalse(constraints["remote_models_required"])
        self.assertFalse(constraints["model_weights_shipped_by_minerva"])
        self.assertFalse(constraints["models_downloaded_by_registry"])
        self.assertEqual(constraints["benchmark_claims"], "none")

    def test_candidates_include_required_metadata(self) -> None:
        candidates = _load_registry()["candidates"]

        self.assertGreaterEqual(len(candidates), 1)
        for candidate in candidates:
            with self.subTest(candidate=candidate.get("id")):
                self.assert_required_string(candidate, "id")
                self.assert_required_string(candidate, "name")
                self.assert_required_string(candidate, "provider_model")
                self.assert_required_string(candidate, "parameter_count_notes")
                self.assert_required_string(candidate, "quantization_expectation")
                self.assert_required_string(candidate, "license_provenance_notes")
                self.assert_required_string(candidate, "provider_command")
                self.assert_required_string(candidate, "candidate_status")

                parameter_count = candidate["parameter_count_millions"]
                self.assertIsInstance(parameter_count, int)
                self.assertGreater(parameter_count, 0)
                self.assertLessEqual(parameter_count, 500)

                runtime_path = candidate["runtime_path"]
                self.assert_required_string(runtime_path, "runtime")
                self.assert_required_string(runtime_path, "minerva_adapter")
                self.assert_required_string(runtime_path, "artifact_format")

                hardware_target = candidate["hardware_target"]
                self.assertEqual(hardware_target["device"], "CPU")
                self.assertFalse(hardware_target["gpu_required"])
                self.assert_required_string(hardware_target, "target_environment")

                self.assertIn(
                    "No benchmark result claimed",
                    candidate["eval_notes"],
                )

    def test_first_eval_candidate_matches_default_local_provider(self) -> None:
        candidates = _load_registry()["candidates"]
        first_eval_candidates = [
            candidate
            for candidate in candidates
            if candidate["candidate_status"] == "first_eval_candidate"
        ]

        self.assertEqual(len(first_eval_candidates), 1)
        first = first_eval_candidates[0]
        self.assertEqual(first["provider_model"], "qwen2.5-coder:0.5b-instruct")
        self.assertEqual(
            first["runtime_path"]["base_url"],
            "http://localhost:11434/v1/chat/completions",
        )
        self.assertEqual(
            first["runtime_path"]["minerva_adapter"],
            "LocalOpenAICompatibleProvider",
        )

    def test_example_eval_artifact_contract_is_not_a_benchmark_claim(self) -> None:
        registry = _load_registry()
        artifact = _load_json(ARTIFACT_EXAMPLE_PATH)
        candidate_ids = {candidate["id"] for candidate in registry["candidates"]}

        self.assertEqual(
            artifact["schema_version"],
            "minerva.cpu_model_eval_artifact.v0",
        )
        self.assertEqual(artifact["artifact_status"], "example_contract_not_benchmark")
        self.assertIn(artifact["registry_candidate_id"], candidate_ids)
        self.assertFalse(artifact["benchmark_claim"])
        self.assertFalse(artifact["fixture_report"])
        self.assertFalse(artifact["model_weights_shipped_by_minerva"])
        self.assertFalse(artifact["models_downloaded_by_artifact"])
        self.assertIn("--provider", artifact["command"])
        self.assertIn("local-openai", artifact["command"])

        evidence = artifact["evidence_requirements"]
        self.assertEqual(evidence["minimum_case_count"], 30)
        self.assertEqual(
            evidence["scoring_contract"],
            registry["scoring_contract"],
        )
        self.assertFalse(evidence["gpu_used"])
        self.assertFalse(evidence["remote_models_used"])
        self.assertIn("fallback_behavior", evidence["required_metrics"])
        self.assertEqual(
            sorted(evidence["required_decisions"]),
            ["promote", "reject", "retest"],
        )

    def assert_required_string(self, payload: dict[str, object], key: str) -> None:
        self.assertIn(key, payload)
        self.assertIsInstance(payload[key], str)
        self.assertTrue(payload[key].strip())


def _load_registry() -> dict[str, object]:
    payload = _load_json(REGISTRY_PATH)
    if not isinstance(payload, dict):
        raise AssertionError("registry root must be a JSON object")
    return payload


def _load_json(path: Path) -> dict[str, object]:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise AssertionError(f"{path} root must be a JSON object")
    return payload


if __name__ == "__main__":
    unittest.main()
