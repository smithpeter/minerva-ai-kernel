from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .ci_render import (
    render_ci_artifact_json_from_file,
    render_markdown_summary_from_file,
)
from .daemon import DEFAULT_HOST as MINERVAD_DEFAULT_HOST
from .daemon import DEFAULT_PORT as MINERVAD_DEFAULT_PORT
from .daemon import serve as serve_minervad
from .executor import execute_action
from .observe import DEFAULT_TIMEOUT_SECONDS, observe_command, save_run_record
from .policy import validate_payload
from .providers import ModelProvider
from .providers import check_local_provider_health
from .sdk import Diagnosis, diagnose_file, diagnose_observation
from .types import Decision, Observation
from .verify import render_merge_evidence, render_merge_evidence_markdown_from_file


def main(argv: list[str] | None = None, provider: ModelProvider | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="minerva",
        description="CPU-local failure interpreter for CI/CD, agents, and ops.",
    )
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("doctor", help="Check local Minerva setup.")
    minervad = subparsers.add_parser(
        "minervad",
        help="Run the local-only minervad prototype health server.",
    )
    minervad.add_argument("--host", default=MINERVAD_DEFAULT_HOST)
    minervad.add_argument("--port", type=int, default=MINERVAD_DEFAULT_PORT)
    provider_health = subparsers.add_parser(
        "provider-health",
        help="Check optional local OpenAI-compatible provider reachability.",
    )
    provider_health.add_argument(
        "--base-url",
        default="http://localhost:11434/v1/chat/completions",
        help="Local chat completions endpoint to probe.",
    )
    provider_health.add_argument(
        "--model",
        default="qwen2.5-coder:0.5b-instruct",
        help="Model name to include in the local health request.",
    )
    provider_health.add_argument(
        "--timeout",
        type=float,
        default=2.0,
        help="Health request timeout in seconds.",
    )
    diagnose = subparsers.add_parser("diagnose", help="Diagnose a failure JSON file.")
    diagnose.add_argument("path")
    observe = subparsers.add_parser("observe", help="Observe a command failure.")
    observe.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT_SECONDS,
        metavar="SECONDS",
        help="Maximum command runtime before Minerva records a timeout.",
    )
    observe.add_argument("observed_command", nargs=argparse.REMAINDER)
    policy_check = subparsers.add_parser(
        "policy-check", help="Validate a decision JSON file against policy."
    )
    policy_check.add_argument("path")
    ci_summary = subparsers.add_parser(
        "render-ci-summary",
        help="Render a GitHub Actions markdown summary from a local run.v0 file.",
    )
    ci_summary.add_argument("path")
    ci_artifact = subparsers.add_parser(
        "render-ci-artifact",
        help="Render a minerva_ci_run.v0 JSON artifact from a local run.v0 file.",
    )
    ci_artifact.add_argument(
        "--created-at",
        help="Override the artifact created_at timestamp for reproducible fixtures.",
    )
    ci_artifact.add_argument("path")
    merge_summary = subparsers.add_parser(
        "render-merge-evidence-summary",
        help="Render a markdown merge evidence summary from merge_evidence.v0 JSON.",
    )
    merge_summary.add_argument("path")
    execute = subparsers.add_parser(
        "execute-action",
        help="Explicitly run a policy-gated read-only diagnostic action.",
    )
    execute.add_argument("decision_path")
    execute.add_argument(
        "--observation",
        help="Optional source observation.v0 JSON for bounded follow-up evidence.",
    )
    execute.add_argument(
        "--cwd",
        default=".",
        help="Directory to inspect. Defaults to the current directory.",
    )
    eval_report = subparsers.add_parser(
        "eval-report",
        help="Emit deterministic M1 eval metrics from local fixtures.",
    )
    eval_report.add_argument(
        "--format",
        choices=("json", "markdown"),
        default="json",
        help="Output format.",
    )
    eval_report.add_argument(
        "--target-per-category",
        type=int,
        default=15,
        help="Required corpus cases per category for gap reporting.",
    )
    verify = subparsers.add_parser(
        "verify",
        help="Build merge evidence for a git diff.",
    )
    verify.add_argument(
        "--diff",
        required=True,
        help="Git diff range, for example origin/main...HEAD.",
    )
    verify.add_argument(
        "--format",
        choices=("json", "markdown"),
        default="markdown",
        help="Output format.",
    )
    verify.add_argument(
        "--cwd",
        default=".",
        help="Repository directory to inspect. Defaults to the current directory.",
    )
    verify.add_argument(
        "--include-untracked",
        action="store_true",
        help="Include untracked files from git ls-files --others --exclude-standard.",
    )
    verify.add_argument(
        "--run",
        action="store_true",
        help="Execute selected allowlisted verification checks and include results.",
    )
    verify.add_argument(
        "--output",
        help="Optional path to write the rendered merge evidence.",
    )
    verify.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="Exclude a path or glob from diff evidence. May be provided multiple times.",
    )
    verify_eval_report = subparsers.add_parser(
        "verify-eval-report",
        help="Emit deterministic Minerva Verify eval metrics from local fixtures.",
    )
    verify_eval_report.add_argument(
        "--format",
        choices=("json", "markdown"),
        default="json",
        help="Output format.",
    )
    verify_eval_report.add_argument(
        "--cases",
        default=None,
        help="Path to verify_cases.v0 JSON fixture.",
    )
    args = parser.parse_args(argv)

    if args.command == "doctor":
        print("Minerva doctor: repository skeleton is ready.")
        return

    if args.command == "minervad":
        serve_minervad(host=args.host, port=args.port)
        return

    if args.command == "provider-health":
        health = check_local_provider_health(
            base_url=args.base_url,
            model=args.model,
            timeout=args.timeout,
        )
        print(json.dumps(health.to_dict(), ensure_ascii=True, indent=2, sort_keys=True))
        raise SystemExit(0 if health.reachable else 2)

    if args.command == "diagnose":
        try:
            diagnosis = diagnose_file(args.path, provider=provider)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            print(f"Diagnose failed: {exc}", file=sys.stderr)
            raise SystemExit(1) from exc

        _print_diagnosis(diagnosis)
        if not diagnosis.policy_decision.allowed:
            raise SystemExit(2)
        return

    if args.command == "observe":
        try:
            command = _normalize_observed_command(args.observed_command)
            observation = observe_command(command, timeout_seconds=args.timeout)
            diagnosis = diagnose_observation(observation, provider=provider)
            run_record_path = save_run_record(
                observation=observation,
                decision=diagnosis.decision,
                policy_decision=diagnosis.policy_decision,
                redactions=diagnosis.redactions,
            )
        except (OSError, ValueError) as exc:
            print(f"Observe failed: {exc}", file=sys.stderr)
            raise SystemExit(1) from exc

        _print_diagnosis(diagnosis)
        print(f"Saved: {_display_path(run_record_path)}")
        if not diagnosis.policy_decision.allowed:
            raise SystemExit(2)
        return

    if args.command == "policy-check":
        payload = json.loads(Path(args.path).read_text(encoding="utf-8"))
        decision = validate_payload(payload)
        status = "allowed" if decision.allowed else "blocked"
        print(f"Policy decision: {status}")
        print(f"Reason: {decision.reason}")
        raise SystemExit(0 if decision.allowed else 2)

    if args.command == "render-ci-summary":
        try:
            print(render_markdown_summary_from_file(args.path), end="")
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            print(f"Render CI summary failed: {exc}", file=sys.stderr)
            raise SystemExit(1) from exc
        return

    if args.command == "render-ci-artifact":
        try:
            print(
                render_ci_artifact_json_from_file(
                    args.path,
                    created_at=args.created_at,
                ),
                end="",
            )
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            print(f"Render CI artifact failed: {exc}", file=sys.stderr)
            raise SystemExit(1) from exc
        return

    if args.command == "render-merge-evidence-summary":
        try:
            print(render_merge_evidence_markdown_from_file(args.path), end="")
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            print(f"Render merge evidence summary failed: {exc}", file=sys.stderr)
            raise SystemExit(1) from exc
        return

    if args.command == "execute-action":
        try:
            decision = _load_decision(args.decision_path)
            source_observation = (
                _load_observation(args.observation) if args.observation else None
            )
            executor_observation = execute_action(
                decision,
                cwd=args.cwd,
                observation=source_observation,
            )
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            print(f"Execute action failed: {exc}", file=sys.stderr)
            raise SystemExit(1) from exc

        print(
            json.dumps(
                executor_observation.to_dict(),
                ensure_ascii=True,
                indent=2,
                sort_keys=True,
            )
        )
        policy_allowed = bool(executor_observation.runtime.get("policy_allowed", True))
        raise SystemExit(0 if policy_allowed else 2)

    if args.command == "eval-report":
        from .eval_report import render_m1_eval_report

        try:
            print(
                render_m1_eval_report(
                    output_format=args.format,
                    target_per_category=args.target_per_category,
                ),
                end="",
            )
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            print(f"Eval report failed: {exc}", file=sys.stderr)
            raise SystemExit(1) from exc
        return

    if args.command == "verify":
        try:
            rendered = render_merge_evidence(
                diff_spec=args.diff,
                output_format=args.format,
                repo_path=args.cwd,
                    include_untracked=args.include_untracked,
                    run_checks=args.run,
                    exclude_patterns=args.exclude,
                )
        except (OSError, ValueError) as exc:
            print(f"Verify failed: {exc}", file=sys.stderr)
            raise SystemExit(1) from exc
        _emit_output(rendered, args.output)
        return

    if args.command == "verify-eval-report":
        from .verify_eval import DEFAULT_VERIFY_CASES_PATH, render_verify_eval_report

        cases_path = args.cases or DEFAULT_VERIFY_CASES_PATH
        try:
            print(
                render_verify_eval_report(
                    output_format=args.format,
                    cases_path=cases_path,
                ),
                end="",
            )
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            print(f"Verify eval report failed: {exc}", file=sys.stderr)
            raise SystemExit(1) from exc
        return

    parser.print_help()


def _normalize_observed_command(values: list[str]) -> list[str]:
    command = list(values)
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        raise ValueError("observe requires a command after --")
    return command


def _load_decision(path: str | Path) -> Decision:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("decision JSON must be an object")
    return Decision.from_dict(payload)


def _load_observation(path: str | Path) -> Observation:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("observation JSON must be an object")
    return Observation.from_dict(payload)


def _print_diagnosis(diagnosis: Diagnosis) -> None:
    decision = diagnosis.decision
    policy_decision = diagnosis.policy_decision
    status = "allowed" if policy_decision.allowed else "blocked"

    print(f"Failure: {decision.failure}")
    print(f"Action: {decision.action}")
    print(f"Confidence: {decision.confidence}")
    print(f"Risk: {decision.risk}")
    print(f"Escalation: {str(decision.escalate).lower()}")
    print(f"Policy decision: {status}")
    print(f"Policy decision reason: {policy_decision.reason}")
    if diagnosis.redactions and diagnosis.redactions.count:
        print(
            "Redaction summary: "
            f"count={diagnosis.redactions.count} "
            f"types={', '.join(diagnosis.redactions.types)}"
        )


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        return str(path)


def _emit_output(rendered: str, output: str | None) -> None:
    if output:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rendered, encoding="utf-8")
        return
    print(rendered, end="")


if __name__ == "__main__":
    main()
