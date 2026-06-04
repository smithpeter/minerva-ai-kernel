from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .verify import DiffEntry, build_merge_evidence_from_entries


VERIFY_CASES_SCHEMA_VERSION = "verify_cases.v0"
VERIFY_EVAL_SCHEMA_VERSION = "verify_eval_report.v0"
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_VERIFY_CASES_PATH = REPOSITORY_ROOT / "evals" / "verify_cases_v0.json"


def load_verify_cases(path: str | Path = DEFAULT_VERIFY_CASES_PATH) -> list[dict[str, Any]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("verify cases fixture must be an object")
    if payload.get("schema_version") != VERIFY_CASES_SCHEMA_VERSION:
        raise ValueError(
            f"unsupported verify cases schema_version: {payload.get('schema_version')}"
        )
    cases = payload.get("cases")
    if not isinstance(cases, list):
        raise ValueError("verify cases fixture must contain a cases list")
    return [_validate_case(case) for case in cases]


def build_verify_eval_report(
    *,
    cases_path: str | Path = DEFAULT_VERIFY_CASES_PATH,
) -> dict[str, Any]:
    cases = load_verify_cases(cases_path)
    results = [_evaluate_case(case) for case in cases]
    useful = sum(1 for result in results if result["passed"])
    total = len(results)
    return {
        "schema_version": VERIFY_EVAL_SCHEMA_VERSION,
        "fixtures": {"verify_cases": _relative_path(Path(cases_path))},
        "metrics": {
            "useful_merge_evidence_rate": {
                "useful": useful,
                "total": total,
                "rate": useful / total if total else 0.0,
            }
        },
        "results": results,
    }


def render_verify_eval_json(report: dict[str, Any]) -> str:
    return json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True) + "\n"


def render_verify_eval_markdown(report: dict[str, Any]) -> str:
    metric = report["metrics"]["useful_merge_evidence_rate"]
    lines = [
        "# Minerva Verify Eval Report",
        "",
        "Generated deterministically from local verify cases.",
        "",
        "## Metrics",
        "",
        "| Metric | Result |",
        "| --- | ---: |",
        (
            "| Useful Merge Evidence Rate | "
            f"{metric['useful']}/{metric['total']} ({metric['rate']:.1%}) |"
        ),
        "",
        "## Cases",
        "",
        "| Case | Result |",
        "| --- | --- |",
    ]
    for result in report["results"]:
        status = "PASS" if result["passed"] else "FAIL"
        lines.append(f"| `{result['id']}` | {status} |")
    return "\n".join(lines) + "\n"


def render_verify_eval_report(
    *,
    output_format: str = "json",
    cases_path: str | Path = DEFAULT_VERIFY_CASES_PATH,
) -> str:
    report = build_verify_eval_report(cases_path=cases_path)
    if output_format == "json":
        return render_verify_eval_json(report)
    if output_format == "markdown":
        return render_verify_eval_markdown(report)
    raise ValueError(f"unsupported output format: {output_format}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="python -m minerva_kernel.verify_eval",
        description="Emit deterministic Minerva Verify eval metrics.",
    )
    parser.add_argument(
        "--format",
        choices=("json", "markdown"),
        default="json",
        help="Output format.",
    )
    parser.add_argument(
        "--cases",
        default=str(DEFAULT_VERIFY_CASES_PATH),
        help="Path to verify_cases.v0 JSON fixture.",
    )
    args = parser.parse_args(argv)

    try:
        print(render_verify_eval_report(output_format=args.format, cases_path=args.cases), end="")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"Verify eval report failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


def _evaluate_case(case: dict[str, Any]) -> dict[str, Any]:
    expected = case["expected"]
    report = build_merge_evidence_from_entries(
        [DiffEntry(**entry) for entry in case["entries"]],
        diff_spec=case.get("diff_spec", "main...feature"),
        repository="minerva-ai-kernel",
        created_at="2026-06-04T00:00:00Z",
        added_lines=case.get("added_lines", []),
    )
    summary = report["summary"]
    policy = report["policy"]
    recommended_text = "\n".join(report["recommended_next_steps"])
    expected_areas = set(expected["primary_areas"])
    actual_areas = set(summary["primary_areas"])
    checks = {
        "risk_level": summary["risk_level"] == expected["risk_level"],
        "merge_readiness": summary["merge_readiness"] == expected["merge_readiness"],
        "primary_areas": expected_areas.issubset(actual_areas),
        "policy_decision": policy["decision"] == expected["policy_decision"],
        "recommended_step": expected["recommended_step_contains"] in recommended_text,
    }
    return {
        "id": case["id"],
        "passed": all(checks.values()),
        "checks": checks,
    }


def _validate_case(case: Any) -> dict[str, Any]:
    if not isinstance(case, dict):
        raise ValueError("verify case must be an object")
    for key in ("id", "entries", "expected"):
        if key not in case:
            raise ValueError(f"verify case missing {key}")
    if not isinstance(case["entries"], list) or not case["entries"]:
        raise ValueError(f"verify case {case['id']} entries must be a non-empty list")
    expected = case["expected"]
    if not isinstance(expected, dict):
        raise ValueError(f"verify case {case['id']} expected must be an object")
    for key in (
        "risk_level",
        "merge_readiness",
        "primary_areas",
        "policy_decision",
        "recommended_step_contains",
    ):
        if key not in expected:
            raise ValueError(f"verify case {case['id']} expected missing {key}")
    return case


def _relative_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPOSITORY_ROOT))
    except ValueError:
        return str(path)


if __name__ == "__main__":
    main()

