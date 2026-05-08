from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from minerva_kernel import Decision, Minerva, MockModelProvider, Observation


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    observation = _load_observation(args[0]) if args else _build_observation()

    kernel = Minerva(
        provider=MockModelProvider(
            Decision(
                failure="missing_python_dependency",
                action="inspect_dependencies",
                confidence=0.86,
                risk="low",
                escalate=False,
                evidence=["stderr contains ModuleNotFoundError"],
                reason="Inspect dependency metadata before retrying the test run.",
            )
        )
    )
    diagnosis = kernel.decide(observation)

    print(
        json.dumps(
            {
                "decision": diagnosis.decision.to_dict(),
                "policy_decision": {
                    "allowed": diagnosis.policy_decision.allowed,
                    "reason": diagnosis.policy_decision.reason,
                },
                "execution": {
                    "state": "not_executed",
                    "reason": (
                        "Minerva decisions are advisory until policy allows them; "
                        "this example does not execute the proposed action."
                    ),
                },
            },
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if diagnosis.policy_decision.allowed else 2


def _load_observation(path: str) -> Observation:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("observation JSON must be an object")
    return Observation.from_dict(payload)


def _build_observation() -> Observation:
    return Observation(
        command="python3 -m unittest discover -s tests",
        cwd="/workspace/example-project",
        exit_code=1,
        stdout_tail="",
        stderr_tail="ModuleNotFoundError: No module named 'example_package'",
        duration_ms=742,
        source="sdk_example",
        policy_summary=(
            "local example observation; bounded stderr only; no secrets or "
            "external service credentials"
        ),
        runtime={
            "python": "3.12",
            "platform": "linux",
            "network_status": "not_required",
        },
    )


if __name__ == "__main__":
    raise SystemExit(main())
