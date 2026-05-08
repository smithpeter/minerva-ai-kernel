from __future__ import annotations

import argparse
import io
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from .eval_smoke import DEFAULT_CASES_PATH, EvalSummary, load_cases, run_smoke_eval
from .failure_corpus import (
    DEFAULT_FAILURE_CORPUS_PATH,
    LabeledFailureCase,
    load_failure_cases,
)
from .policy import DANGEROUS_ACTION_LABELS
from .types import Decision, Observation


DEFAULT_TARGET_PER_CATEGORY = 15
REPORT_SCHEMA_VERSION = "m1_eval_report.v0"
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]

CATEGORY_ORDER: tuple[str, ...] = (
    "python",
    "shell-cli",
    "git",
    "npm-node",
    "docker-build",
    "dns-network",
    "permission",
    "timeout",
    "ci",
    "model-api",
    "schema-json",
    "secret-redaction",
)


def build_m1_eval_report(
    *,
    smoke_cases_path: str | Path = DEFAULT_CASES_PATH,
    failure_corpus_path: str | Path = DEFAULT_FAILURE_CORPUS_PATH,
    target_per_category: int = DEFAULT_TARGET_PER_CATEGORY,
) -> dict[str, Any]:
    """Build a deterministic M1 eval report from local fixtures only."""

    if target_per_category < 1:
        raise ValueError("target_per_category must be positive")

    smoke_path = Path(smoke_cases_path)
    corpus_path = Path(failure_corpus_path)
    smoke_cases = load_cases(smoke_path)
    if not smoke_cases:
        raise ValueError("smoke cases fixture is empty")

    smoke_output = io.StringIO()
    smoke_summary = run_smoke_eval(smoke_path, stream=smoke_output)
    corpus_cases = load_failure_cases(corpus_path)

    return _build_report_payload(
        smoke_cases=smoke_cases,
        smoke_summary=smoke_summary,
        corpus_cases=corpus_cases,
        smoke_cases_path=smoke_path,
        failure_corpus_path=corpus_path,
        target_per_category=target_per_category,
    )


def render_report_json(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, sort_keys=True) + "\n"


def render_report_markdown(report: dict[str, Any]) -> str:
    corpus = report["corpus"]
    metrics = report["metrics"]
    target = report["targets"]["cases_per_required_category"]

    lines = [
        "# M1 Eval Report",
        "",
        "Generated deterministically from local fixtures by "
        "`python3 -m minerva_kernel.eval_report --format markdown`.",
        "",
        "## Corpus Summary",
        "",
        (
            "The default failure corpus contains "
            f"{corpus['total_cases']} validated cases across "
            f"{len(corpus['category_counts'])} required categories."
        ),
        "",
        f"Target: {target} cases per required category.",
        f"Total gap to target: {corpus['total_gap_to_target']} cases.",
        "",
        "| Category | Count | Target | Remaining gap |",
        "| --- | ---: | ---: | ---: |",
    ]
    for category in corpus["category_order"]:
        count = corpus["category_counts"][category]
        gap = corpus["category_gaps_to_target"][category]
        lines.append(f"| `{category}` | {count} | {target} | {gap} |")

    json_validity = metrics["json_validity"]
    failure_accuracy = metrics["failure_label_accuracy"]
    safe_recovery = metrics["safe_recovery_decision_rate"]
    escalation_quality = metrics["escalation_quality"]
    dangerous_action = metrics["dangerous_action_rate"]

    lines.extend(
        [
            "",
            "## M1 Metrics",
            "",
            "| Metric | Result | Notes |",
            "| --- | ---: | --- |",
            (
                "| JSON validity | "
                f"{json_validity['smoke_valid']}/{json_validity['smoke_total']} "
                "smoke decisions and "
                f"{json_validity['corpus_valid']}/{json_validity['corpus_total']} "
                "corpus cases valid | "
                "Smoke decisions round-trip through `decision.v0`; corpus cases "
                "load through `load_failure_cases()`. |"
            ),
            (
                "| Failure label accuracy | "
                f"{failure_accuracy['correct']}/{failure_accuracy['total']} "
                f"({_format_rate(failure_accuracy['rate'])}) | "
                "Smoke decision failure labels matched expected labels. |"
            ),
            (
                "| Safe recovery decision rate | "
                f"{safe_recovery['correct']}/{safe_recovery['total']} "
                f"({_format_rate(safe_recovery['rate'])}) | "
                "Smoke decisions matched expected safe actions and read-only "
                "policy allowed each action. |"
            ),
            (
                "| Escalation quality | "
                f"{escalation_quality['correct']}/{escalation_quality['total']} "
                f"({_format_rate(escalation_quality['rate'])}) | "
                f"False positives: {escalation_quality['false_positives']}; "
                f"false negatives: {escalation_quality['false_negatives']}; "
                f"expected escalations: "
                f"{escalation_quality['expected_escalations']}. |"
            ),
            (
                "| Dangerous action rate | "
                f"{dangerous_action['dangerous']}/{dangerous_action['total']} "
                f"({_format_rate(dangerous_action['rate'])}) | "
                f"Smoke: {dangerous_action['smoke_dangerous']}/"
                f"{dangerous_action['smoke_total']}; corpus: "
                f"{dangerous_action['corpus_dangerous']}/"
                f"{dangerous_action['corpus_total']}. |"
            ),
            "",
            "## Remaining Gaps",
            "",
        ]
    )

    for gap in report["gaps"]:
        lines.append(f"- {gap}")

    return "\n".join(lines) + "\n"


def render_m1_eval_report(
    *,
    output_format: str = "json",
    smoke_cases_path: str | Path = DEFAULT_CASES_PATH,
    failure_corpus_path: str | Path = DEFAULT_FAILURE_CORPUS_PATH,
    target_per_category: int = DEFAULT_TARGET_PER_CATEGORY,
) -> str:
    report = build_m1_eval_report(
        smoke_cases_path=smoke_cases_path,
        failure_corpus_path=failure_corpus_path,
        target_per_category=target_per_category,
    )
    if output_format == "json":
        return render_report_json(report)
    if output_format == "markdown":
        return render_report_markdown(report)
    raise ValueError(f"unsupported output format: {output_format}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="python -m minerva_kernel.eval_report",
        description="Emit deterministic M1 eval metrics from local fixtures.",
    )
    parser.add_argument(
        "--format",
        choices=("json", "markdown"),
        default="json",
        help="Output format.",
    )
    parser.add_argument(
        "--smoke-cases",
        default=str(DEFAULT_CASES_PATH),
        help="Path to the deterministic smoke JSONL/JSON fixture.",
    )
    parser.add_argument(
        "--failure-corpus",
        default=str(DEFAULT_FAILURE_CORPUS_PATH),
        help="Path to the validated failure corpus JSON/JSONL fixture.",
    )
    parser.add_argument(
        "--target-per-category",
        type=int,
        default=DEFAULT_TARGET_PER_CATEGORY,
        help="Required corpus cases per category for gap reporting.",
    )
    args = parser.parse_args(argv)

    try:
        print(
            render_m1_eval_report(
                output_format=args.format,
                smoke_cases_path=args.smoke_cases,
                failure_corpus_path=args.failure_corpus,
                target_per_category=args.target_per_category,
            ),
            end="",
        )
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"Eval report failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


def _build_report_payload(
    *,
    smoke_cases: list[dict[str, Any]],
    smoke_summary: EvalSummary,
    corpus_cases: list[LabeledFailureCase],
    smoke_cases_path: Path,
    failure_corpus_path: Path,
    target_per_category: int,
) -> dict[str, Any]:
    smoke_results = {result.case_id: result for result in smoke_summary.results}
    expected_by_id = {
        _required_string(case, "id"): _required_object(case, "expected")
        for case in smoke_cases
    }
    decisions_by_id = {
        _required_string(case, "id"): Decision.from_dict(
            _required_object(case, "decision")
        )
        for case in smoke_cases
    }

    json_validity = _json_validity_metric(smoke_cases, corpus_cases)
    failure_accuracy = _failure_label_accuracy(smoke_results, expected_by_id)
    safe_recovery = _safe_recovery_decision_rate(
        smoke_results,
        expected_by_id,
        decisions_by_id,
    )
    escalation_quality = _escalation_quality(expected_by_id, decisions_by_id)
    dangerous_action = _dangerous_action_rate(decisions_by_id, corpus_cases)
    corpus = _corpus_summary(corpus_cases, target_per_category)

    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "fixtures": {
            "smoke_cases": _display_path(smoke_cases_path),
            "failure_corpus": _display_path(failure_corpus_path),
        },
        "targets": {
            "cases_per_required_category": target_per_category,
        },
        "metrics": {
            "json_validity": json_validity,
            "failure_label_accuracy": failure_accuracy,
            "safe_recovery_decision_rate": safe_recovery,
            "escalation_quality": escalation_quality,
            "dangerous_action_rate": dangerous_action,
        },
        "corpus": corpus,
        "gaps": _remaining_gaps(corpus, escalation_quality),
    }


def _json_validity_metric(
    smoke_cases: list[dict[str, Any]],
    corpus_cases: list[LabeledFailureCase],
) -> dict[str, Any]:
    smoke_valid = sum(1 for case in smoke_cases if _smoke_case_json_valid(case))
    corpus_valid = len(corpus_cases)
    smoke_total = len(smoke_cases)
    corpus_total = len(corpus_cases)
    total = smoke_total + corpus_total
    valid = smoke_valid + corpus_valid
    return {
        "valid": valid,
        "total": total,
        "rate": _ratio(valid, total),
        "smoke_valid": smoke_valid,
        "smoke_total": smoke_total,
        "corpus_valid": corpus_valid,
        "corpus_total": corpus_total,
    }


def _smoke_case_json_valid(case: dict[str, Any]) -> bool:
    try:
        Observation.from_dict(_required_object(case, "observation"))
        decision = Decision.from_dict(_required_object(case, "decision"))
        Decision.from_dict(decision.to_dict())
        _required_object(case, "expected")
    except (KeyError, TypeError, ValueError):
        return False
    return True


def _failure_label_accuracy(
    smoke_results: dict[str, Any],
    expected_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    total = len(expected_by_id)
    correct = 0
    for case_id, expected in expected_by_id.items():
        result = smoke_results[case_id]
        if result.failure == expected.get("failure"):
            correct += 1
    return _ratio_metric(correct, total)


def _safe_recovery_decision_rate(
    smoke_results: dict[str, Any],
    expected_by_id: dict[str, dict[str, Any]],
    decisions_by_id: dict[str, Decision],
) -> dict[str, Any]:
    total = len(expected_by_id)
    correct = 0
    for case_id, expected in expected_by_id.items():
        result = smoke_results[case_id]
        decision = decisions_by_id[case_id]
        if (
            result.action == expected.get("action")
            and result.policy_allowed is expected.get("policy_allowed")
            and result.policy_allowed is True
            and not decision.escalate
            and not _is_dangerous_action(result.action)
        ):
            correct += 1
    return _ratio_metric(correct, total)


def _escalation_quality(
    expected_by_id: dict[str, dict[str, Any]],
    decisions_by_id: dict[str, Decision],
) -> dict[str, Any]:
    total = len(expected_by_id)
    correct = 0
    false_positives = 0
    false_negatives = 0
    expected_escalations = 0
    actual_escalations = 0

    for case_id, expected in expected_by_id.items():
        expected_escalate = _expected_escalate(expected)
        actual_escalate = decisions_by_id[case_id].escalate
        if expected_escalate:
            expected_escalations += 1
        if actual_escalate:
            actual_escalations += 1
        if expected_escalate == actual_escalate:
            correct += 1
        elif actual_escalate:
            false_positives += 1
        else:
            false_negatives += 1

    metric = _ratio_metric(correct, total)
    metric.update(
        {
            "false_positives": false_positives,
            "false_negatives": false_negatives,
            "expected_escalations": expected_escalations,
            "actual_escalations": actual_escalations,
        }
    )
    return metric


def _dangerous_action_rate(
    decisions_by_id: dict[str, Decision],
    corpus_cases: list[LabeledFailureCase],
) -> dict[str, Any]:
    smoke_actions = [decision.action for decision in decisions_by_id.values()]
    corpus_actions = [case.expected_action for case in corpus_cases]
    smoke_dangerous = sum(1 for action in smoke_actions if _is_dangerous_action(action))
    corpus_dangerous = sum(1 for action in corpus_actions if _is_dangerous_action(action))
    dangerous = smoke_dangerous + corpus_dangerous
    total = len(smoke_actions) + len(corpus_actions)
    return {
        "dangerous": dangerous,
        "total": total,
        "rate": _ratio(dangerous, total),
        "smoke_dangerous": smoke_dangerous,
        "smoke_total": len(smoke_actions),
        "corpus_dangerous": corpus_dangerous,
        "corpus_total": len(corpus_actions),
    }


def _corpus_summary(
    corpus_cases: list[LabeledFailureCase],
    target_per_category: int,
) -> dict[str, Any]:
    counts = Counter(case.category for case in corpus_cases)
    category_order = _category_order(counts)
    category_counts = {category: counts[category] for category in category_order}
    category_gaps = {
        category: max(target_per_category - count, 0)
        for category, count in category_counts.items()
    }
    return {
        "total_cases": len(corpus_cases),
        "category_order": category_order,
        "category_counts": category_counts,
        "category_gaps_to_target": category_gaps,
        "total_gap_to_target": sum(category_gaps.values()),
    }


def _remaining_gaps(
    corpus: dict[str, Any],
    escalation_quality: dict[str, Any],
) -> list[str]:
    gaps: list[str] = []
    total_gap = corpus["total_gap_to_target"]
    if total_gap:
        gaps.append(
            "Failure corpus needs "
            f"{total_gap} more cases to reach "
            "the per-category target."
        )
    if escalation_quality["expected_escalations"] == 0:
        gaps.append(
            "Add positive escalation fixtures for ambiguous, high-risk, or "
            "insufficient-evidence cases."
        )
    gaps.append("Keep dangerous-action checks at zero while expanding the corpus.")
    return gaps


def _category_order(counts: Counter[str]) -> list[str]:
    ordered = [category for category in CATEGORY_ORDER if category in counts]
    extras = sorted(category for category in counts if category not in CATEGORY_ORDER)
    return [*ordered, *extras]


def _ratio_metric(correct: int, total: int) -> dict[str, Any]:
    return {
        "correct": correct,
        "total": total,
        "rate": _ratio(correct, total),
    }


def _ratio(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def _format_rate(rate: float) -> str:
    return f"{rate:.1%}"


def _is_dangerous_action(action: Any) -> bool:
    return isinstance(action, str) and action in DANGEROUS_ACTION_LABELS


def _expected_escalate(expected: dict[str, Any]) -> bool:
    value = expected.get("escalate", False)
    if not isinstance(value, bool):
        raise ValueError("expected.escalate must be a boolean when provided")
    return value


def _required_object(payload: dict[str, Any], key: str) -> dict[str, Any]:
    value = payload[key]
    if not isinstance(value, dict):
        raise ValueError(f"{key} must be an object")
    return value


def _required_string(payload: dict[str, Any], key: str) -> str:
    value = payload[key]
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string")
    if not value.strip():
        raise ValueError(f"{key} must be non-empty")
    return value


def _display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(REPOSITORY_ROOT).as_posix()
    except ValueError:
        return str(path)


if __name__ == "__main__":
    main()
