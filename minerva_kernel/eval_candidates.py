from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from .redaction import RedactionSummary, merge_redaction_summaries, redact_value
from .types import Decision, Observation


EVAL_CANDIDATE_SCHEMA_VERSION = "minerva_eval_candidate.v0"


def render_eval_candidates_jsonl(paths: Iterable[str | Path]) -> str:
    candidates = [build_eval_candidate_from_run(path) for path in paths]
    return "".join(json.dumps(item, sort_keys=True) + "\n" for item in candidates)


def build_eval_candidate_from_run(path: str | Path) -> dict[str, Any]:
    run_path = Path(path)
    payload = json.loads(run_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("run record JSON must be an object")
    if payload.get("schema_version") != "run.v0":
        raise ValueError("run record schema_version must be run.v0")

    observation_payload = _required_object(payload, "observation")
    decision_payload = _required_object(payload, "decision")
    policy_payload = _required_object(payload, "policy_decision")

    observation = Observation.from_dict(observation_payload)
    decision = Decision.from_dict(decision_payload)
    policy_allowed = policy_payload.get("allowed")
    if not isinstance(policy_allowed, bool):
        raise ValueError("policy_decision.allowed must be a boolean")
    policy_reason = policy_payload.get("reason")
    if not isinstance(policy_reason, str) or not policy_reason.strip():
        raise ValueError("policy_decision.reason must be a non-empty string")

    raw_candidate: dict[str, Any] = {
        "schema_version": EVAL_CANDIDATE_SCHEMA_VERSION,
        "source": {
            "kind": "run.v0",
            "path": str(run_path),
            "created_at": _required_string(payload, "created_at"),
        },
        "review": {
            "status": "needs_human_review",
            "approved_for_corpus": False,
            "notes": [
                "Generated from a local run record.",
                "Do not merge into eval corpora without human label review.",
            ],
        },
        "case": {
            "id": f"candidate-{run_path.stem}",
            "category": "unreviewed",
            "observation": observation.to_dict(),
            "model_decision": decision.to_dict(),
            "policy_decision": {
                "allowed": policy_allowed,
                "reason": policy_reason,
            },
            "suggested_expected": {
                "failure": decision.failure,
                "action": decision.action,
                "escalate": decision.escalate,
                "safe_recovery_eligible": (
                    policy_allowed
                    and not decision.escalate
                    and decision.risk == "low"
                ),
            },
        },
    }

    redacted = redact_value(raw_candidate)
    if not isinstance(redacted.value, dict):
        raise ValueError("redacted eval candidate must be an object")
    candidate = redacted.value
    redactions = merge_redaction_summaries(
        redacted.summary,
        *_nested_redaction_summaries(candidate),
    )
    if redactions.count:
        candidate["redactions"] = redactions.to_dict()
    return candidate


def _nested_redaction_summaries(candidate: dict[str, Any]) -> list[RedactionSummary]:
    summaries: list[RedactionSummary] = []
    case = candidate.get("case")
    if not isinstance(case, dict):
        return summaries
    for key in ("observation", "model_decision"):
        value = case.get(key)
        if not isinstance(value, dict):
            continue
        summary = value.get("redactions")
        if isinstance(summary, dict):
            count = summary.get("count")
            types = summary.get("types")
            if isinstance(count, int) and isinstance(types, list):
                summaries.append(
                    RedactionSummary(
                        count=count,
                        types=tuple(str(item) for item in types),
                    )
                )
    return summaries


def _required_object(payload: dict[str, Any], key: str) -> dict[str, Any]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"{key} must be an object")
    return value


def _required_string(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string")
    return value
