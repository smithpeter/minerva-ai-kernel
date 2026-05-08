from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .policy import PolicyRuntime
from .types import INSTRUCTION_SET_V0, Observation


DEFAULT_FAILURE_CORPUS_PATH = (
    Path(__file__).resolve().parents[1] / "evals" / "failure_cases_m0_slice.json"
)

REQUIRED_M0_CATEGORIES = frozenset(
    {
        "python",
        "shell-cli",
        "npm-node",
        "docker-build",
        "dns-network",
        "permission",
        "timeout",
        "secret-redaction",
    }
)


@dataclass(frozen=True)
class LabeledFailureCase:
    case_id: str
    category: str
    observation: Observation
    expected_failure: str
    expected_action: str
    policy_allowed: bool
    policy_reason: str
    rationale: str


def load_failure_cases(
    path: str | Path = DEFAULT_FAILURE_CORPUS_PATH,
) -> list[LabeledFailureCase]:
    """Load and validate labeled failure cases from JSON or JSONL."""

    cases_path = Path(path)
    payloads = _load_payloads(cases_path)
    if not payloads:
        raise ValueError("failure corpus is empty")
    return [
        _parse_case(payload, f"{cases_path}:{index}")
        for index, payload in enumerate(payloads, 1)
    ]


def _load_payloads(path: Path) -> list[dict[str, Any]]:
    if path.suffix == ".jsonl":
        cases: list[dict[str, Any]] = []
        for line_number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), 1
        ):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            payload = json.loads(stripped)
            cases.append(_require_object_value(payload, f"{path}:{line_number}"))
        return cases

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("failure corpus JSON must contain a list of cases")
    return [
        _require_object_value(item, f"{path}:{index}")
        for index, item in enumerate(payload, 1)
    ]


def _parse_case(payload: dict[str, Any], label: str) -> LabeledFailureCase:
    try:
        case_id = _required_string(payload, "id")
        category = _required_string(payload, "category")
        if category not in REQUIRED_M0_CATEGORIES:
            raise ValueError(f"unsupported category: {category}")

        observation = Observation.from_dict(_required_object(payload, "observation"))
        expected_failure = _required_string(payload, "expected_failure")
        expected_action = _required_string(payload, "expected_action")
        if expected_action not in INSTRUCTION_SET_V0:
            raise ValueError(f"unsupported expected_action: {expected_action}")

        policy_expectation = _required_object(payload, "policy_expectation")
        policy_allowed = _required_bool(policy_expectation, "allowed")
        policy_reason = _required_string(policy_expectation, "reason")
        _validate_policy_expectation(expected_action, policy_allowed)

        redaction_expectation = payload.get("redaction_expectation")
        if category == "secret-redaction" and redaction_expectation is None:
            raise ValueError("secret-redaction cases require redaction_expectation")
        if redaction_expectation is not None:
            _validate_redaction_expectation(
                observation,
                _require_object_value(redaction_expectation, "redaction_expectation"),
            )

        rationale = _required_string(payload, "rationale")
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"{label}: {exc}") from exc

    return LabeledFailureCase(
        case_id=case_id,
        category=category,
        observation=observation,
        expected_failure=expected_failure,
        expected_action=expected_action,
        policy_allowed=policy_allowed,
        policy_reason=policy_reason,
        rationale=rationale,
    )


def _validate_policy_expectation(expected_action: str, policy_allowed: bool) -> None:
    policy_decision = PolicyRuntime().validate_payload({"action": expected_action})
    if policy_decision.allowed is not policy_allowed:
        expected_label = "allowed" if policy_allowed else "blocked"
        actual_label = "allowed" if policy_decision.allowed else "blocked"
        raise ValueError(
            "policy_expectation.allowed must match read-only policy for "
            f"{expected_action}: expected {expected_label}, got {actual_label}"
        )


def _validate_redaction_expectation(
    observation: Observation,
    expectation: dict[str, Any],
) -> None:
    count_min = _required_int(expectation, "count_min")
    expected_types = _required_string_list(expectation, "types")
    redactions = observation.to_dict().get("redactions", {})
    if not isinstance(redactions, dict):
        raise ValueError("redaction_expectation was set but observation has none")

    actual_count = redactions.get("count", 0)
    if not isinstance(actual_count, int) or isinstance(actual_count, bool):
        raise ValueError("observation redaction count must be an integer")
    if actual_count < count_min:
        raise ValueError(
            f"expected at least {count_min} redactions, got {actual_count}"
        )

    actual_types = redactions.get("types", [])
    if isinstance(actual_types, str) or not isinstance(actual_types, list):
        raise ValueError("observation redaction types must be a list")
    missing_types = sorted(set(expected_types) - {str(item) for item in actual_types})
    if missing_types:
        raise ValueError(f"missing redaction types: {', '.join(missing_types)}")


def _required_object(payload: dict[str, Any], key: str) -> dict[str, Any]:
    return _require_object_value(payload[key], key)


def _require_object_value(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def _required_string(payload: dict[str, Any], key: str) -> str:
    value = payload[key]
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string")
    if not value.strip():
        raise ValueError(f"{key} must be non-empty")
    return value


def _required_bool(payload: dict[str, Any], key: str) -> bool:
    value = payload[key]
    if not isinstance(value, bool):
        raise ValueError(f"{key} must be a boolean")
    return value


def _required_int(payload: dict[str, Any], key: str) -> int:
    value = payload[key]
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{key} must be an integer")
    if value < 1:
        raise ValueError(f"{key} must be positive")
    return value


def _required_string_list(payload: dict[str, Any], key: str) -> list[str]:
    value = payload[key]
    if isinstance(value, str) or not isinstance(value, list):
        raise ValueError(f"{key} must be a list")
    items = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"{key} must contain non-empty strings")
        items.append(item)
    if not items:
        raise ValueError(f"{key} must be non-empty")
    return items
