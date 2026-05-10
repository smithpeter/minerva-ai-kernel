from __future__ import annotations

import importlib.util
import json
import re
import sys
import unittest
from collections import Counter
from pathlib import Path

from minerva_kernel.types import INSTRUCTION_SET_V0


ROOT = Path(__file__).resolve().parents[1]
CORPUS_PATH = ROOT / "corpus" / "real_world_v0" / "entries.jsonl"
SCHEMA_KEYS = {
    "id",
    "repo",
    "run_url",
    "raw_log_redacted",
    "expected_failure_label",
    "expected_action",
    "license_note",
}

EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PRIVATE_PATH_RE = re.compile(r"(?<![\w.-])/(?:Users|home)/")
TOKEN_VALUE_RE = re.compile(
    r"\b(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}|"
    r"sk-[A-Za-z0-9]{20,}|Bearer\s+[A-Za-z0-9._~+/=-]{12,}|"
    r"(?:AKIA|ASIA)[A-Z0-9]{16})\b",
    re.IGNORECASE,
)
UUID_RE = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
    re.IGNORECASE,
)


def load_entries() -> list[dict[str, str]]:
    entries = []
    for line in CORPUS_PATH.read_text(encoding="utf-8").splitlines():
        if line.strip():
            entries.append(json.loads(line))
    return entries


def load_builder_module():
    script_path = ROOT / "scripts" / "build_real_world_corpus.py"
    spec = importlib.util.spec_from_file_location("build_real_world_corpus", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load build_real_world_corpus.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class RealWorldCorpusTests(unittest.TestCase):
    def test_real_world_v0_has_exactly_50_schema_valid_entries(self) -> None:
        entries = load_entries()

        self.assertEqual(len(entries), 50)
        self.assertEqual(len({entry["id"] for entry in entries}), 50)
        for entry in entries:
            self.assertEqual(set(entry), SCHEMA_KEYS)
            self.assertRegex(entry["id"], r"^real-world-v0-\d{3}$")
            self.assertRegex(
                entry["run_url"],
                rf"^https://github\.com/{re.escape(entry['repo'])}/actions/runs/\d+$",
            )
            self.assertIn(entry["expected_action"], INSTRUCTION_SET_V0)
            self.assertTrue(entry["expected_failure_label"].strip())
            self.assertGreater(len(entry["raw_log_redacted"].splitlines()), 3)
            self.assertTrue(entry["license_note"].strip())

    def test_real_world_v0_uses_three_public_oss_python_repos(self) -> None:
        repo_counts = Counter(entry["repo"] for entry in load_entries())

        self.assertEqual(
            repo_counts,
            Counter(
                {
                    "pytest-dev/pytest": 17,
                    "encode/httpx": 17,
                    "fastapi/fastapi": 16,
                }
            ),
        )
        notes = {entry["repo"]: entry["license_note"] for entry in load_entries()}
        self.assertIn("MIT", notes["pytest-dev/pytest"])
        self.assertIn("BSD-3-Clause", notes["encode/httpx"])
        self.assertIn("MIT", notes["fastapi/fastapi"])

    def test_real_world_v0_logs_are_redacted(self) -> None:
        for entry in load_entries():
            log = entry["raw_log_redacted"]
            self.assertIsNone(EMAIL_RE.search(log), entry["id"])
            self.assertIsNone(PRIVATE_PATH_RE.search(log), entry["id"])
            self.assertIsNone(TOKEN_VALUE_RE.search(log), entry["id"])
            self.assertIsNone(UUID_RE.search(log), entry["id"])
            self.assertNotIn("TOKEN", log.upper(), entry["id"])

    def test_builder_source_list_matches_checked_in_entries(self) -> None:
        builder = load_builder_module()
        entries = load_entries()
        source_urls = [source.run_url for source in builder.DEFAULT_SOURCES]

        self.assertEqual(len(source_urls), 50)
        self.assertEqual([entry["run_url"] for entry in entries], source_urls)


if __name__ == "__main__":
    unittest.main()
