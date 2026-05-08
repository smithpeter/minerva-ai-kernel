from __future__ import annotations

import argparse
import json
from pathlib import Path

from .policy import validate_payload


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="minerva",
        description="CPU-local failure interpreter for CI/CD, agents, and ops.",
    )
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("doctor", help="Check local Minerva setup.")
    diagnose = subparsers.add_parser("diagnose", help="Diagnose a failure JSON file.")
    diagnose.add_argument("path")
    observe = subparsers.add_parser("observe", help="Observe a command failure.")
    observe.add_argument("observed_command", nargs=argparse.REMAINDER)
    policy_check = subparsers.add_parser(
        "policy-check", help="Validate a decision JSON file against policy."
    )
    policy_check.add_argument("path")
    args = parser.parse_args(argv)

    if args.command == "doctor":
        print("Minerva doctor: repository skeleton is ready.")
        return

    if args.command == "diagnose":
        raise SystemExit("diagnose is planned for M0 and not implemented yet")

    if args.command == "observe":
        raise SystemExit("observe is planned for M0 and not implemented yet")

    if args.command == "policy-check":
        payload = json.loads(Path(args.path).read_text(encoding="utf-8"))
        decision = validate_payload(payload)
        status = "allowed" if decision.allowed else "blocked"
        print(f"Policy decision: {status}")
        print(f"Reason: {decision.reason}")
        raise SystemExit(0 if decision.allowed else 2)

    parser.print_help()


if __name__ == "__main__":
    main()
