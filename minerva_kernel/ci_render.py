from __future__ import annotations

import json
import os
from copy import deepcopy
from datetime import datetime, timezone
from html import escape as html_escape
from pathlib import Path
from typing import Any, Mapping

from .redaction import RedactionSummary, merge_redaction_summaries, redact_value


CI_ARTIFACT_SCHEMA_VERSION = "minerva_ci_run.v0"
ARTIFACT_TAIL_CHARS = 12000
MARKDOWN_EXCERPT_CHARS = 1200


def load_run_record(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("run record JSON must be an object")
    if payload.get("schema_version") != "run.v0":
        raise ValueError(f"unsupported run record schema_version: {payload.get('schema_version')}")
    return payload


def render_markdown_summary(
    run_record: Mapping[str, Any],
    *,
    run_record_path: str | Path | None = None,
) -> str:
    safe_record, redactions = _safe_run_record(run_record)
    summary = _summary_payload(safe_record, redactions)
    observation = _mapping(safe_record.get("observation"))
    decision = _mapping(safe_record.get("decision"))
    policy_decision = _mapping(safe_record.get("policy_decision"))

    status_text = _markdown_status(summary["status"])
    path_text = str(run_record_path) if run_record_path is not None else "local run.v0"
    policy_status = "allowed" if summary["policy_allowed"] else "blocked"
    stdout_tail = _markdown_excerpt(str(observation.get("stdout_tail", "")))
    stderr_tail = _markdown_excerpt(str(observation.get("stderr_tail", "")))
    redaction_text = _redaction_text(redactions)

    if summary["policy_allowed"]:
        policy_note = (
            "Minerva classified the failure from bounded evidence and proposed a "
            "read-only diagnostic action. CI should not execute this action automatically."
        )
    else:
        policy_note = (
            "Minerva classified the failure, but policy blocked the decision. Treat the "
            "decision as audit evidence only."
        )

    lines = [
        "# Minerva CI Summary",
        "",
        f"Status: {status_text}",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| Command | {_inline_code(observation.get('command', ''))} |",
        f"| Working directory | {_inline_code(observation.get('cwd', ''))} |",
        f"| Exit code | {_inline_code(summary['observed_exit_code'])} |",
        f"| Duration | {_inline_code(str(observation.get('duration_ms', '')) + ' ms')} |",
        f"| Run record | {_inline_code(path_text)} |",
        "",
        "## Failure Interpretation",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| Failure | {_inline_code(summary['failure'])} |",
        f"| Diagnostic action | {_inline_code(summary['action'])} |",
        f"| Confidence | {_inline_code(summary['confidence'])} |",
        f"| Risk | {_inline_code(summary['risk'])} |",
        f"| Escalation requested | {_inline_code(str(summary['escalate']).lower())} |",
        "",
        policy_note,
        "",
        "## Safety Gate",
        "",
        "| Check | Result |",
        "| --- | --- |",
        "| Auto-repair | disabled |",
        "| Model input redacted | yes |",
        "| Artifact redacted | yes |",
        f"| Policy decision | {policy_status} |",
        f"| Policy reason | {_inline_code(policy_decision.get('reason', ''))} |",
        "| GitHub API credentials | not required |",
        "",
        "## Evidence Excerpts",
        "",
        "stdout tail:",
        "",
        "```text",
        stdout_tail,
        "```",
        "",
        "stderr tail:",
        "",
        "```text",
        stderr_tail,
        "```",
        "",
        "Redactions:",
        "",
        "```text",
        redaction_text,
        "```",
        "",
    ]
    return "\n".join(lines)


def render_markdown_summary_from_file(path: str | Path) -> str:
    return render_markdown_summary(load_run_record(path), run_record_path=path)


def build_ci_artifact(
    run_record: Mapping[str, Any],
    *,
    env: Mapping[str, str] | None = None,
    created_at: str | None = None,
) -> dict[str, Any]:
    safe_record, redactions = _safe_run_record(run_record)
    return {
        "schema_version": CI_ARTIFACT_SCHEMA_VERSION,
        "created_at": created_at or _artifact_created_at(safe_record),
        "ci": _ci_metadata(os.environ if env is None else env),
        "summary": _summary_payload(safe_record, redactions),
        "run_record": safe_record,
        "safety": {
            "auto_repair": False,
            "model_input_redacted": True,
            "artifact_redacted": True,
            "policy_gated": bool(_mapping(safe_record.get("policy_decision"))),
            "github_api_credentials_required": False,
            "notes": [
                "The diagnostic action is not executed automatically.",
                "Only bounded stdout and stderr tails are persisted.",
                "Consumers should rely on policy_allowed before using the decision.",
            ],
        },
    }


def render_ci_artifact_json(
    run_record: Mapping[str, Any],
    *,
    env: Mapping[str, str] | None = None,
    created_at: str | None = None,
) -> str:
    artifact = build_ci_artifact(run_record, env=env, created_at=created_at)
    return json.dumps(artifact, ensure_ascii=True, indent=2, sort_keys=True) + "\n"


def render_ci_artifact_json_from_file(
    path: str | Path,
    *,
    env: Mapping[str, str] | None = None,
    created_at: str | None = None,
) -> str:
    return render_ci_artifact_json(
        load_run_record(path),
        env=env,
        created_at=created_at,
    )


def _safe_run_record(
    run_record: Mapping[str, Any],
) -> tuple[dict[str, Any], RedactionSummary | None]:
    copied = deepcopy(dict(run_record))
    redaction_result = redact_value(copied)
    safe_record = _bound_run_record(redaction_result.value)
    existing = _record_redactions(safe_record)
    redactions = _merge_optional_redactions(existing, redaction_result.summary)
    if redactions and redactions.count:
        safe_record["redactions"] = redactions.to_dict()
    return safe_record, redactions


def _bound_run_record(record: Any) -> dict[str, Any]:
    if not isinstance(record, dict):
        raise ValueError("run record JSON must be an object")
    if record.get("schema_version") != "run.v0":
        raise ValueError(f"unsupported run record schema_version: {record.get('schema_version')}")

    observation = _mapping(record.get("observation"))
    for field in ("stdout_tail", "stderr_tail"):
        if field in observation:
            observation[field] = _tail(str(observation[field]), ARTIFACT_TAIL_CHARS)
    return record


def _summary_payload(
    run_record: Mapping[str, Any],
    redactions: RedactionSummary | None,
) -> dict[str, Any]:
    observation = _mapping(run_record.get("observation"))
    decision = _mapping(run_record.get("decision"))
    policy_decision = _mapping(run_record.get("policy_decision"))

    policy_allowed = bool(policy_decision.get("allowed", False))
    observed_exit_code = observation.get("exit_code")
    status = _status(observed_exit_code, policy_allowed, bool(policy_decision))
    redaction_count = redactions.count if redactions else 0
    redaction_types = list(redactions.types) if redactions else []
    return {
        "status": status,
        "observed_exit_code": observed_exit_code,
        "failure": decision.get("failure", ""),
        "action": decision.get("action", ""),
        "confidence": decision.get("confidence", 0.0),
        "risk": decision.get("risk", ""),
        "escalate": bool(decision.get("escalate", False)),
        "policy_allowed": policy_allowed,
        "policy_reason": policy_decision.get("reason", ""),
        "redaction_count": redaction_count,
        "redaction_types": redaction_types,
    }


def _status(
    observed_exit_code: Any,
    policy_allowed: bool,
    has_policy_decision: bool,
) -> str:
    if not has_policy_decision:
        return "minerva_error"
    if not policy_allowed:
        return "blocked_by_policy"
    if observed_exit_code == 0:
        return "passed"
    return "failed_policy_allowed"


def _ci_metadata(env: Mapping[str, str]) -> dict[str, Any]:
    github_present = env.get("GITHUB_ACTIONS", "").lower() == "true" or any(
        key.startswith("GITHUB_") for key in env
    )
    return {
        "provider": "github_actions" if github_present else "local",
        "workflow": env.get("GITHUB_WORKFLOW", ""),
        "job": env.get("GITHUB_JOB", ""),
        "run_id": env.get("GITHUB_RUN_ID", ""),
        "attempt": _optional_int(env.get("GITHUB_RUN_ATTEMPT")),
        "event_name": env.get("GITHUB_EVENT_NAME", ""),
        "ref": env.get("GITHUB_REF", ""),
        "sha": env.get("GITHUB_SHA", ""),
    }


def _artifact_created_at(run_record: Mapping[str, Any]) -> str:
    value = run_record.get("created_at")
    if isinstance(value, str) and value:
        return value
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _record_redactions(record: Mapping[str, Any]) -> RedactionSummary | None:
    root_summary = _redaction_summary_from_dict(record.get("redactions"))
    if root_summary:
        return root_summary

    summaries: list[RedactionSummary] = []
    for key in ("observation", "decision"):
        value = record.get(key)
        if isinstance(value, dict):
            summary = _redaction_summary_from_dict(value.get("redactions"))
            if summary:
                summaries.append(summary)
    if not summaries:
        return None
    merged = merge_redaction_summaries(*summaries)
    return merged if merged.count else None


def _redaction_summary_from_dict(value: Any) -> RedactionSummary | None:
    if not isinstance(value, dict):
        return None
    count = value.get("count", 0)
    if not isinstance(count, int) or isinstance(count, bool) or count <= 0:
        return None
    types = value.get("types", [])
    if isinstance(types, str) or not isinstance(types, list):
        return None
    return RedactionSummary(count=count, types=tuple(str(item) for item in types))


def _merge_optional_redactions(
    *summaries: RedactionSummary | None,
) -> RedactionSummary | None:
    present = [summary for summary in summaries if summary and summary.count]
    if not present:
        return None
    merged = merge_redaction_summaries(*present)
    return merged if merged.count else None


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _tail(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[-limit:]


def _markdown_excerpt(text: str) -> str:
    if not text:
        return "(empty)"
    if len(text) <= MARKDOWN_EXCERPT_CHARS:
        return text
    return (
        f"[truncated to last {MARKDOWN_EXCERPT_CHARS} chars]\n"
        f"{text[-MARKDOWN_EXCERPT_CHARS:]}"
    )


def _redaction_text(redactions: RedactionSummary | None) -> str:
    if not redactions or not redactions.count:
        return "none"
    return f"count={redactions.count} types={','.join(redactions.types)}"


def _markdown_status(status: Any) -> str:
    labels = {
        "passed": "passed",
        "failed_policy_allowed": "failed, policy allowed diagnostic action",
        "blocked_by_policy": "blocked by policy",
        "minerva_error": "minerva error",
    }
    return labels.get(str(status), str(status))


def _inline_code(value: Any) -> str:
    text = _single_line(str(value))
    if "`" in text:
        return f"<code>{html_escape(text)}</code>"
    return f"`{_escape_table(text)}`"


def _single_line(text: str) -> str:
    return text.replace("\r", "\\r").replace("\n", "\\n")


def _escape_table(text: str) -> str:
    return text.replace("|", "\\|")


def _optional_int(value: str | None) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except ValueError:
        return None
