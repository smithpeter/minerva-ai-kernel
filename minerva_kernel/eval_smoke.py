from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TextIO

from .cli import diagnose_observation
from .providers import MockModelProvider
from .types import Decision, Observation


DEFAULT_CASES_PATH = (
    Path(__file__).resolve().parents[1] / "evals" / "smoke_cases.jsonl"
)


@dataclass(frozen=True)
class EvalCaseResult:
    case_id: str
    passed: bool
    failures: tuple[str, ...]
    failure: str | None = None
    action: str | None = None
    policy_allowed: bool | None = None
    redaction_types: tuple[str, ...] = ()


@dataclass(frozen=True)
class EvalSummary:
    total: int
    passed: int
    failed: int
    results: tuple[EvalCaseResult, ...]

    @property
    def safe_recovery_decision_rate(self) -> float:
        if self.total == 0:
            return 0.0
        return self.passed / self.total


def run_smoke_eval(
    cases_path: str | Path = DEFAULT_CASES_PATH,
    stream: TextIO | None = None,
) -> EvalSummary:
    output = stream or sys.stdout
    cases = load_cases(cases_path)
    if not cases:
        raise ValueError("eval cases fixture is empty")
    results = tuple(_evaluate_case(case) for case in cases)
    summary = EvalSummary(
        total=len(results),
        passed=sum(1 for result in results if result.passed),
        failed=sum(1 for result in results if not result.passed),
        results=results,
    )
    _print_summary(summary, output)
    return summary


def load_cases(path: str | Path) -> list[dict[str, Any]]:
    cases_path = Path(path)
    if cases_path.suffix == ".jsonl":
        return _load_jsonl(cases_path)

    payload = json.loads(cases_path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("eval case JSON must contain a list of cases")
    return [_require_object(item, f"case[{index}]") for index, item in enumerate(payload)]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="python -m minerva_kernel.eval_smoke",
        description="Run Minerva's deterministic eval smoke corpus.",
    )
    parser.add_argument(
        "cases_path",
        nargs="?",
        default=str(DEFAULT_CASES_PATH),
        help="JSONL or JSON eval case fixture path.",
    )
    args = parser.parse_args(argv)

    try:
        summary = run_smoke_eval(args.cases_path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"Eval smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    raise SystemExit(0 if summary.failed == 0 else 2)


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        payload = json.loads(stripped)
        cases.append(_require_object(payload, f"{path}:{line_number}"))
    return cases


def _evaluate_case(case: dict[str, Any]) -> EvalCaseResult:
    case_id = _required_string(case, "id")
    failures: list[str] = []
    failure: str | None = None
    action: str | None = None
    policy_allowed: bool | None = None
    redaction_types: tuple[str, ...] = ()

    try:
        observation = Observation.from_dict(_required_object(case, "observation"))
        configured_decision = Decision.from_dict(_required_object(case, "decision"))
        expected = _required_object(case, "expected")

        provider = MockModelProvider(configured_decision)
        diagnosis = diagnose_observation(observation, provider=provider)
        decision_payload = diagnosis.decision.to_dict()
        if decision_payload.get("schema_version") != "decision.v0":
            failures.append("serialized decision schema_version is not decision.v0")
        Decision.from_dict(decision_payload)

        failure = diagnosis.decision.failure
        action = diagnosis.decision.action
        policy_allowed = diagnosis.policy_decision.allowed
        redaction_count = 0
        if diagnosis.redactions:
            redaction_types = diagnosis.redactions.types
            redaction_count = diagnosis.redactions.count

        _compare_expected(diagnosis, expected, failures)
        _check_redactions(
            provider=provider,
            decision_payload=decision_payload,
            expected=expected,
            redaction_count=redaction_count,
            redaction_types=redaction_types,
            failures=failures,
        )
    except (KeyError, TypeError, ValueError) as exc:
        failures.append(str(exc))

    return EvalCaseResult(
        case_id=case_id,
        passed=not failures,
        failures=tuple(failures),
        failure=failure,
        action=action,
        policy_allowed=policy_allowed,
        redaction_types=redaction_types,
    )


def _compare_expected(
    diagnosis: Any,
    expected: dict[str, Any],
    failures: list[str],
) -> None:
    expected_failure = expected.get("failure")
    if expected_failure is not None and diagnosis.decision.failure != expected_failure:
        failures.append(
            f"expected failure {expected_failure}, got {diagnosis.decision.failure}"
        )

    expected_action = expected.get("action")
    if expected_action is not None and diagnosis.decision.action != expected_action:
        failures.append(
            f"expected action {expected_action}, got {diagnosis.decision.action}"
        )

    expected_policy_allowed = expected.get("policy_allowed")
    if expected_policy_allowed is not None and not isinstance(
        expected_policy_allowed, bool
    ):
        failures.append("policy_allowed must be a boolean")
    elif expected_policy_allowed is not None and (
        diagnosis.policy_decision.allowed is not expected_policy_allowed
    ):
        expected_status = "allowed" if expected_policy_allowed else "blocked"
        actual_status = "allowed" if diagnosis.policy_decision.allowed else "blocked"
        failures.append(
            f"expected policy {expected_status}, got {actual_status}: "
            f"{diagnosis.policy_decision.reason}"
        )


def _check_redactions(
    provider: MockModelProvider,
    decision_payload: dict[str, Any],
    expected: dict[str, Any],
    redaction_count: int,
    redaction_types: tuple[str, ...],
    failures: list[str],
) -> None:
    expected_types = _optional_string_list(expected, "redaction_types")
    missing_types = sorted(set(expected_types) - set(redaction_types))
    if missing_types:
        failures.append(f"missing redaction types: {', '.join(missing_types)}")

    redaction_count_min = expected.get("redaction_count_min")
    if redaction_count_min is not None:
        if not isinstance(redaction_count_min, int) or isinstance(
            redaction_count_min, bool
        ):
            failures.append("redaction_count_min must be an integer")
        else:
            actual_count = int(
                decision_payload.get("redactions", {}).get("count", 0)
            )
            prompt_count = sum(
                _count_redactions_in_message(message)
                for call in provider.calls
                for message in call
            )
            actual_count = max(actual_count, prompt_count, redaction_count)
            if actual_count < redaction_count_min:
                failures.append(
                    f"expected at least {redaction_count_min} redactions, "
                    f"got {actual_count}"
                )

    forbidden_strings = _optional_string_list(expected, "forbidden_strings")
    if forbidden_strings:
        inspected_payload = json.dumps(
            {"provider_calls": provider.calls, "decision": decision_payload},
            sort_keys=True,
        )
        for forbidden in forbidden_strings:
            if forbidden in inspected_payload:
                failures.append(f"forbidden string leaked: {forbidden}")


def _print_summary(summary: EvalSummary, stream: TextIO) -> None:
    print("Minerva eval smoke v0", file=stream)
    print(
        f"Cases: {summary.passed}/{summary.total} passed, {summary.failed} failed",
        file=stream,
    )
    print(
        "Safe Recovery Decision Rate: "
        f"{summary.passed}/{summary.total} "
        f"({summary.safe_recovery_decision_rate:.1%})",
        file=stream,
    )
    for result in summary.results:
        status = "PASS" if result.passed else "FAIL"
        policy = _policy_label(result.policy_allowed)
        details = [
            f"failure={result.failure or 'unknown'}",
            f"action={result.action or 'unknown'}",
            f"policy={policy}",
        ]
        if result.redaction_types:
            details.append(f"redactions={','.join(result.redaction_types)}")
        print(f"- {status} {result.case_id} {' '.join(details)}", file=stream)
        for failure in result.failures:
            print(f"  - {failure}", file=stream)


def _policy_label(policy_allowed: bool | None) -> str:
    if policy_allowed is None:
        return "unknown"
    return "allowed" if policy_allowed else "blocked"


def _count_redactions_in_message(message: dict[str, str]) -> int:
    return sum(value.count("[REDACTED:") for value in message.values())


def _required_object(payload: dict[str, Any], key: str) -> dict[str, Any]:
    value = payload[key]
    return _require_object(value, key)


def _require_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def _required_string(payload: dict[str, Any], key: str) -> str:
    value = payload[key]
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string")
    if not value:
        raise ValueError(f"{key} must be non-empty")
    return value


def _optional_string_list(payload: dict[str, Any], key: str) -> list[str]:
    value = payload.get(key, [])
    if isinstance(value, str) or not isinstance(value, list):
        raise ValueError(f"{key} must be a list")
    return [str(item) for item in value]


if __name__ == "__main__":
    main()
