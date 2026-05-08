from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from minerva_kernel.cli import main


class CliTests(unittest.TestCase):
    def test_cli_help(self) -> None:
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            try:
                main([])
            except SystemExit as exc:
                self.assertEqual(exc.code, 0)

        self.assertIn("CPU-local failure interpreter", stdout.getvalue())

    def test_cli_policy_check_shows_block_reason(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            payload_path = Path(tmpdir) / "decision.json"
            payload_path.write_text(
                json.dumps({"action": "check_logs", "command": "rm -rf /tmp/example"}),
                encoding="utf-8",
            )

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                with self.assertRaises(SystemExit) as raised:
                    main(["policy-check", str(payload_path)])

        self.assertEqual(raised.exception.code, 2)
        out = stdout.getvalue()
        self.assertIn("Policy decision: blocked", out)
        self.assertIn("Reason: blocked destructive command attempt", out)


if __name__ == "__main__":
    unittest.main()
