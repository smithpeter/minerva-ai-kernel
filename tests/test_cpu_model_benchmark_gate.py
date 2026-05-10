from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check-cpu-benchmark-evidence.py"
EXAMPLE_ARTIFACT = ROOT / "evals" / "cpu_model_report_artifact.example.json"


def load_gate():
    spec = importlib.util.spec_from_file_location("check_cpu_benchmark_evidence", SCRIPT)
    if spec is None or spec.loader is None:
        raise AssertionError("could not load CPU benchmark gate")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class CPUModelBenchmarkGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.gate = load_gate()

    def test_example_artifact_is_rejected_as_non_benchmark(self) -> None:
        summary = self.gate.validate_benchmark_artifact(EXAMPLE_ARTIFACT)

        self.assertFalse(summary["ready"])
        self.assertIn("artifact_status must be 'real_local_benchmark'", summary["errors"])
        self.assertIn("benchmark_claim must be True", summary["errors"])

    def test_valid_synthetic_real_benchmark_artifact_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "artifact.json"
            path.write_text(json.dumps(_valid_artifact()), encoding="utf-8")

            summary = self.gate.validate_benchmark_artifact(path)

        self.assertTrue(summary["ready"])
        self.assertEqual(summary["errors"], [])
        self.assertEqual(summary["report_decision"], "promote")
        self.assertEqual(summary["case_count"], 30)

    def test_fixture_runtime_is_rejected(self) -> None:
        artifact = _valid_artifact()
        artifact["report"]["candidate"]["runtime"] = "fixture"
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "artifact.json"
            path.write_text(json.dumps(artifact), encoding="utf-8")

            summary = self.gate.validate_benchmark_artifact(path)

        self.assertFalse(summary["ready"])
        self.assertIn("report.candidate.runtime must not be fixture", summary["errors"])

    def test_cli_exits_nonzero_for_example_artifact(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), str(EXAMPLE_ARTIFACT)],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )

        self.assertEqual(completed.returncode, 1)
        payload = json.loads(completed.stdout)
        self.assertFalse(payload["ready"])


def _valid_artifact() -> dict[str, object]:
    required_metrics = [
        "json_validity",
        "failure_label_accuracy",
        "safe_recovery_decision_rate",
        "escalation_quality",
        "dangerous_action_rate",
        "latency_ms",
        "fallback_behavior",
    ]
    return {
        "schema_version": "minerva.cpu_model_eval_artifact.v0",
        "artifact_status": "real_local_benchmark",
        "created_at": "2026-05-11T00:00:00Z",
        "registry_candidate_id": "qwen2_5_coder_0_5b_instruct_ollama",
        "provider_model": "qwen2.5-coder:0.5b-instruct",
        "benchmark_claim": True,
        "fixture_report": False,
        "model_weights_shipped_by_minerva": False,
        "models_downloaded_by_artifact": False,
        "evidence_requirements": {
            "minimum_case_count": 30,
            "gpu_used": False,
            "remote_models_used": False,
            "required_metrics": required_metrics,
        },
        "report": {
            "schema_version": "minerva.cpu_model_eval_report.v0",
            "decision": "promote",
            "candidate": {
                "name": "qwen2.5-coder:0.5b-instruct",
                "device": "cpu",
                "runtime": "ollama-openai-compatible",
            },
            "corpus": {"case_count": 30},
            "minimum_path": {
                "gpu_used": False,
                "remote_models_used": False,
                "model_weights_shipped_by_minerva": False,
            },
            "metrics": {metric: {} for metric in required_metrics},
        },
    }


if __name__ == "__main__":
    unittest.main()
