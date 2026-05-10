from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .types import INSTRUCTION_SET_V0


EVAL_CANDIDATE_REVIEW_SCHEMA_VERSION = "minerva_eval_candidate_review.v0"
REVIEW_STATUSES = frozenset({"accepted", "rejected", "deferred"})


@dataclass(frozen=True)
class EvalCandidateLedgerSummary:
    schema_version: str
    total_reviews: int
    accepted: int
    rejected: int
    deferred: int
    duplicate_candidate_ids: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "minerva_eval_candidate_ledger_summary.v0",
            "review_schema_version": self.schema_version,
            "total_reviews": self.total_reviews,
            "accepted": self.accepted,
            "rejected": self.rejected,
            "deferred": self.deferred,
            "duplicate_candidate_ids": self.duplicate_candidate_ids,
        }


def validate_eval_candidate_ledger_jsonl(
    path: str | Path,
) -> EvalCandidateLedgerSummary:
    reviews = list(load_eval_candidate_ledger_jsonl(path))
    seen: set[str] = set()
    duplicate_count = 0
    counts = {"accepted": 0, "rejected": 0, "deferred": 0}
    for review in reviews:
        candidate_id = _required_string(review, "candidate_id")
        if candidate_id in seen:
            duplicate_count += 1
        seen.add(candidate_id)
        status = review["status"]
        counts[status] += 1
    if duplicate_count:
        raise ValueError(f"duplicate candidate_id entries: {duplicate_count}")
    return EvalCandidateLedgerSummary(
        schema_version=EVAL_CANDIDATE_REVIEW_SCHEMA_VERSION,
        total_reviews=len(reviews),
        accepted=counts["accepted"],
        rejected=counts["rejected"],
        deferred=counts["deferred"],
        duplicate_candidate_ids=duplicate_count,
    )


def load_eval_candidate_ledger_jsonl(path: str | Path) -> Iterable[dict[str, Any]]:
    ledger_path = Path(path)
    for line_number, line in enumerate(
        ledger_path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"line {line_number}: invalid JSON: {exc.msg}") from exc
        if not isinstance(payload, dict):
            raise ValueError(f"line {line_number}: review entry must be an object")
        yield validate_eval_candidate_review(payload, line_number=line_number)


def validate_eval_candidate_review(
    payload: dict[str, Any],
    *,
    line_number: int | None = None,
) -> dict[str, Any]:
    prefix = f"line {line_number}: " if line_number is not None else ""
    if payload.get("schema_version") != EVAL_CANDIDATE_REVIEW_SCHEMA_VERSION:
        raise ValueError(
            f"{prefix}schema_version must be {EVAL_CANDIDATE_REVIEW_SCHEMA_VERSION}"
        )
    _required_string(payload, "candidate_id", prefix=prefix)
    _required_string(payload, "reviewer", prefix=prefix)
    _required_string(payload, "reviewed_at", prefix=prefix)
    _required_non_empty_list(payload, "notes", prefix=prefix)

    status = payload.get("status")
    if status not in REVIEW_STATUSES:
        raise ValueError(f"{prefix}status must be one of {sorted(REVIEW_STATUSES)}")
    approved = payload.get("approved_for_corpus")
    if not isinstance(approved, bool):
        raise ValueError(f"{prefix}approved_for_corpus must be a boolean")

    if status == "accepted":
        if approved is not True:
            raise ValueError(f"{prefix}accepted reviews must approve corpus use")
        _validate_expected(payload.get("expected"), prefix=prefix)
    else:
        if approved is not False:
            raise ValueError(f"{prefix}{status} reviews must not approve corpus use")
        if "expected" in payload:
            raise ValueError(f"{prefix}{status} reviews must not include expected")

    return dict(payload)


def _validate_expected(value: Any, *, prefix: str) -> None:
    if not isinstance(value, dict):
        raise ValueError(f"{prefix}accepted reviews must include expected object")
    failure = value.get("failure")
    if not isinstance(failure, str) or not failure.strip():
        raise ValueError(f"{prefix}expected.failure must be a non-empty string")
    action = value.get("action")
    if action not in INSTRUCTION_SET_V0:
        raise ValueError(f"{prefix}expected.action is unsupported: {action}")
    for field in ("escalate", "safe_recovery_eligible"):
        if not isinstance(value.get(field), bool):
            raise ValueError(f"{prefix}expected.{field} must be a boolean")


def _required_string(
    payload: dict[str, Any],
    field: str,
    *,
    prefix: str = "",
) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{prefix}{field} must be a non-empty string")
    return value


def _required_non_empty_list(
    payload: dict[str, Any],
    field: str,
    *,
    prefix: str,
) -> list[Any]:
    value = payload.get(field)
    if isinstance(value, str) or not isinstance(value, list) or not value:
        raise ValueError(f"{prefix}{field} must be a non-empty list")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise ValueError(f"{prefix}{field} must contain non-empty strings")
    return value
