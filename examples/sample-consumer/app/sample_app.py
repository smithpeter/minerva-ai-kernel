"""Minimal failing entry point for the Minerva sample-consumer template.

This script imports a deliberately-nonexistent package so the
failure is reproducible in any environment — including local
machines that may have pyyaml or other common packages pre-installed.

Minerva's baseline interpreter classifies the resulting
ModuleNotFoundError as ``missing_dependency`` with an
``inspect_dependencies`` next action. That is the entire demo.
"""

import minerva_sample_missing_dep  # noqa: F401


def main() -> None:
    print("unreachable: the import above raises ModuleNotFoundError")


if __name__ == "__main__":
    main()
