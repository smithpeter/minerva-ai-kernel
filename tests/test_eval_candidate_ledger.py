from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from minerva_kernel.cli import main
from minerva_kernel.eval_candidate_ledger import (
    EVAL_CANDIDATE_REVIEW_SCHEMA_VERSION,
    validate_eval_candidate_ledger_jsonl,
    validate_eval_candidate_review,
)


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_LEDGER = ROOT / "evals" / "eval_candidate_ledger.example.jsonl"


class EvalCandidateLedgerTests(unittest.TestCase):
    def test_example_ledger_validates(self) -> None:
        summary = validate_eval_candidate_ledger_jsonl(EXAMPLE_LEDGER)

        self.assertEqual(summary.total_reviews, 3)
        self.assertEqual(summary.accepted, 1)
        self.assertEqual(summary.rejected, 1)
        self.assertEqual(summary.deferred, 1)
        self.assertEqual(summary.duplicate_candidate_ids, 0)

    def test_accepted_review_requires_expected_labels(self) -> None:
        payload = _review(status="accepted", approved_for_corpus=True)
        payload.pop("expected")

        with self.assertRaisesRegex(ValueError, "expected object"):
            validate_eval_candidate_review(payload)

    def test_rejected_review_cannot_approve_corpus_use(self) -> None:
        payload = _review(status="rejected", approved_for_corpus=True)
        payload.pop("expected")

        with self.assertRaisesRegex(ValueError, "must not approve corpus use"):
            validate_eval_candidate_review(payload)

    def test_duplicate_candidate_ids_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "ledger.jsonl"
            first = _review(candidate_id="candidate-1")
            second = _review(candidate_id="candidate-1")
            path.write_text(
                json.dumps(first) + "\n" + json.dumps(second) + "\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "duplicate candidate_id"):
                validate_eval_candidate_ledger_jsonl(path)

    def test_cli_validates_eval_ledger(self) -> None:
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            main(["validate-eval-ledger", str(EXAMPLE_LEDGER)])

        payload = json.loads(stdout.getvalue())
        self.assertEqual(
            payload["schema_version"],
            "minerva_eval_candidate_ledger_summary.v0",
        )
        self.assertEqual(payload["review_schema_version"], EVAL_CANDIDATE_REVIEW_SCHEMA_VERSION)
        self.assertEqual(payload["total_reviews"], 3)


def _review(
    *,
    candidate_id: str = "candidate-1",
    status: str = "accepted",
    approved_for_corpus: bool = True,
) -> dict[str, object]:
    return {
        "schema_version": EVAL_CANDIDATE_REVIEW_SCHEMA_VERSION,
        "candidate_id": candidate_id,
        "status": status,
        "reviewer": "eval-reviewer",
        "reviewed_at": "2026-05-11T00:00:00Z",
        "approved_for_corpus": approved_for_corpus,
        "notes": ["reviewed by a human"],
        "expected": {
            "failure": "missing_dependency",
            "action": "inspect_dependencies",
            "escalate": False,
            "safe_recovery_eligible": True,
        },
    }


if __name__ == "__main__":
    unittest.main()
