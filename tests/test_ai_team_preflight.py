from __future__ import annotations

import subprocess
import unittest


class AiTeamPreflightTests(unittest.TestCase):
    def test_preflight_reports_core_fields(self) -> None:
        completed = subprocess.run(
            ["bash", "scripts/ai-team-preflight.sh"],
            capture_output=True,
            check=True,
            text=True,
        )
        output = completed.stdout

        self.assertIn("schema_version=ai_team_preflight.v0", output)
        self.assertIn("root=", output)
        self.assertIn("dirty_count=", output)
        self.assertIn("pending_count=", output)
        self.assertIn("codex_available=", output)
        self.assertIn("claude_available=", output)
        self.assertIn("plan_eng_review_workflow=present", output)
        self.assertIn("systemd_timer=", output)
        self.assertIn("ready=", output)
        self.assertIn("reason=", output)

    def test_coordinator_runs_from_current_checkout_without_explicit_root(self) -> None:
        completed = subprocess.run(
            ["bash", "scripts/ai-team-coordinator.sh"],
            capture_output=True,
            check=True,
            text=True,
        )

        self.assertIn(
            "Minerva AI team coordinator: pending tasks=",
            completed.stdout,
        )
        self.assertNotIn("/Users/zouyongming/projects/minerva-ai-kernel", completed.stderr)


if __name__ == "__main__":
    unittest.main()
