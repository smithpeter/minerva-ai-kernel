from __future__ import annotations

import argparse


def main() -> None:
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
    args = parser.parse_args()

    if args.command == "doctor":
        print("Minerva doctor: repository skeleton is ready.")
        return

    if args.command == "diagnose":
        raise SystemExit("diagnose is planned for M0 and not implemented yet")

    if args.command == "observe":
        raise SystemExit("observe is planned for M0 and not implemented yet")

    parser.print_help()


if __name__ == "__main__":
    main()

