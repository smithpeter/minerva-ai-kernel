from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .planner import build_prompt
from .policy import validate_action
from .providers import ModelProvider
from .redaction import RedactionSummary, merge_redaction_summaries
from .router import LocalLLMRouter
from .types import Decision, Observation, PolicyDecision


@dataclass(frozen=True)
class Diagnosis:
    decision: Decision
    policy_decision: PolicyDecision
    redactions: RedactionSummary | None


class Minerva:
    """Small Python SDK facade for policy-gated local decisions."""

    def __init__(self, provider: ModelProvider | None = None) -> None:
        self.provider = provider

    def decide(self, observation: Observation) -> Diagnosis:
        return diagnose_observation(observation, provider=self.provider)

    def decide_file(self, path: str | Path) -> Diagnosis:
        return diagnose_file(path, provider=self.provider)


def diagnose_file(path: str | Path, provider: ModelProvider | None = None) -> Diagnosis:
    observation = _load_observation(path)
    return diagnose_observation(observation, provider=provider)


def diagnose_observation(
    observation: Observation, provider: ModelProvider | None = None
) -> Diagnosis:
    redacted_observation = observation.redacted()
    messages = build_prompt(redacted_observation)
    decision = LocalLLMRouter(provider=provider).propose(messages)
    policy_decision = validate_action(decision)
    redactions = _merge_optional_redactions(
        redacted_observation.redactions,
        decision.redactions,
    )
    return Diagnosis(decision, policy_decision, redactions)


def _load_observation(path: str | Path) -> Observation:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("observation JSON must be an object")
    return Observation.from_dict(payload)


def _merge_optional_redactions(
    *summaries: RedactionSummary | None,
) -> RedactionSummary | None:
    present = [summary for summary in summaries if summary and summary.count]
    if not present:
        return None
    merged = merge_redaction_summaries(*present)
    return merged if merged.count else None
