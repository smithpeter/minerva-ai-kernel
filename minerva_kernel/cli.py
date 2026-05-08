from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .ci_render import (
    render_ci_artifact_json_from_file,
    render_markdown_summary_from_file,
)
from .observe import DEFAULT_TIMEOUT_SECONDS, observe_command, save_run_record
from .policy import validate_payload
from .providers import ModelProvider
from .sdk import Diagnosis, diagnose_file, diagnose_observation


def main(argv: list[str] | None = None, provider: ModelProvider | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="minerva",
        description="CPU-local failure interpreter for CI/CD, agents, and ops.",
    )
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("doctor", help="Check local Minerva setup.")
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
    args = parser.parse_args(argv)

    if args.command == "doctor":
        print("Minerva doctor: repository skeleton is ready.")
        return

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

    parser.print_help()


def _normalize_observed_command(values: list[str]) -> list[str]:
    command = list(values)
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        raise ValueError("observe requires a command after --")
    return command


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


if __name__ == "__main__":
    main()
