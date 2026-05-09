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
        self.assertIn("systemd_timer=", output)
        self.assertIn("ready=", output)
        self.assertIn("reason=", output)


if __name__ == "__main__":
    unittest.main()
