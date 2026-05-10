from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "minervad-diagnose-smoke.py"


def load_smoke():
    spec = importlib.util.spec_from_file_location("minervad_diagnose_smoke", SCRIPT)
    if spec is None or spec.loader is None:
        raise AssertionError("could not load minervad smoke script")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class MinervadSmokeScriptTests(unittest.TestCase):
    def test_run_smoke_verifies_health_and_diagnosis(self) -> None:
        smoke = load_smoke()

        payload = smoke.run_smoke()

        self.assertEqual(payload["schema_version"], "minerva.minervad_smoke.v0")
        self.assertTrue(payload["ready"])
        self.assertTrue(payload["checks"]["health_ok"])
        self.assertTrue(payload["checks"]["diagnosis_schema"])
        self.assertTrue(payload["checks"]["policy_allowed"])
        self.assertTrue(payload["checks"]["not_executed"])
        self.assertEqual(payload["diagnosis_action"], "inspect_dependencies")
        self.assertEqual(payload["execution_state"], "not_executed")

    def test_script_outputs_json(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(SCRIPT)],
            cwd=ROOT,
            capture_output=True,
            check=True,
            text=True,
        )

        payload = json.loads(completed.stdout)
        self.assertTrue(payload["ready"])


if __name__ == "__main__":
    unittest.main()
