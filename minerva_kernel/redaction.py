from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


REDACTION_MARKER = "[REDACTED:{kind}]"


@dataclass(frozen=True)
class RedactionSummary:
    count: int
    types: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {"count": self.count, "types": list(self.types)}


@dataclass(frozen=True)
class RedactionResult:
    value: Any
    summary: RedactionSummary


@dataclass(frozen=True)
class _Rule:
    kind: str
    pattern: re.Pattern[str]
    replacement: str


_PRIVATE_KEY_PATTERN = re.compile(
    r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----.*?-----END [A-Z0-9 ]*PRIVATE KEY-----",
    re.DOTALL,
)

_RULES: tuple[_Rule, ...] = (
    _Rule(
        "private_key",
        _PRIVATE_KEY_PATTERN,
        REDACTION_MARKER.format(kind="private_key"),
    ),
    _Rule(
        "bearer_token",
        re.compile(r"\b(Bearer\s+)[A-Za-z0-9._~+/=-]{12,}", re.IGNORECASE),
        r"\1" + REDACTION_MARKER.format(kind="bearer_token"),
    ),
    _Rule(
        "github_token",
        re.compile(
            r"\b(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})\b"
        ),
        REDACTION_MARKER.format(kind="github_token"),
    ),
    _Rule(
        "cloud_credential",
        re.compile(r"\b(?:A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}\b"),
        REDACTION_MARKER.format(kind="cloud_credential"),
    ),
    _Rule(
        "cloud_credential",
        re.compile(
            r"\b(AWS_SECRET_ACCESS_KEY|GOOGLE_API_KEY|AZURE_CLIENT_SECRET|AccountKey)\s*[:=]\s*(?!\[REDACTED:)([^\s,;]+)",
            re.IGNORECASE,
        ),
        r"\1=" + REDACTION_MARKER.format(kind="cloud_credential"),
    ),
    _Rule(
        "api_key",
        re.compile(r"\b(sk-[A-Za-z0-9]{20,}|AIza[0-9A-Za-z_-]{20,})\b"),
        REDACTION_MARKER.format(kind="api_key"),
    ),
    _Rule(
        "api_key",
        re.compile(
            r"\b([A-Za-z0-9_.-]*(?:api[_-]?key|x-api-key|token)[A-Za-z0-9_.-]*)\s*[:=]\s*(?!\[REDACTED:)([^\s,;]+)",
            re.IGNORECASE,
        ),
        r"\1=" + REDACTION_MARKER.format(kind="api_key"),
    ),
    _Rule(
        "password",
        re.compile(
            r"\b([A-Za-z0-9_.-]*(?:password|passwd|pwd)[A-Za-z0-9_.-]*)\s*[:=]\s*(?!\[REDACTED:)([^\s,;]+)",
            re.IGNORECASE,
        ),
        r"\1=" + REDACTION_MARKER.format(kind="password"),
    ),
)
_TYPE_ORDER = tuple(dict.fromkeys(rule.kind for rule in _RULES))


def empty_redaction_summary() -> RedactionSummary:
    return RedactionSummary(count=0, types=())


def redact_text(text: str) -> RedactionResult:
    redacted = text
    count = 0
    kinds: list[str] = []
    for rule in _RULES:
        redacted, replacements = rule.pattern.subn(rule.replacement, redacted)
        if replacements:
            count += replacements
            if rule.kind not in kinds:
                kinds.append(rule.kind)
    return RedactionResult(redacted, RedactionSummary(count=count, types=tuple(kinds)))


def redact_value(value: Any) -> RedactionResult:
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, list):
        values: list[Any] = []
        summaries: list[RedactionSummary] = []
        for item in value:
            result = redact_value(item)
            values.append(result.value)
            summaries.append(result.summary)
        return RedactionResult(values, _merge_summaries(summaries))
    if isinstance(value, tuple):
        values = []
        summaries = []
        for item in value:
            result = redact_value(item)
            values.append(result.value)
            summaries.append(result.summary)
        return RedactionResult(tuple(values), _merge_summaries(summaries))
    if isinstance(value, dict):
        values: dict[Any, Any] = {}
        summaries = []
        for key, item in value.items():
            key_result = redact_value(key)
            item_result = redact_value(item)
            values[key_result.value] = item_result.value
            summaries.extend((key_result.summary, item_result.summary))
        return RedactionResult(values, _merge_summaries(summaries))
    return RedactionResult(value, empty_redaction_summary())


def merge_redaction_summaries(*summaries: RedactionSummary) -> RedactionSummary:
    return _merge_summaries(summaries)


def _merge_summaries(summaries: tuple[RedactionSummary, ...] | list[RedactionSummary]) -> RedactionSummary:
    count = 0
    seen: set[str] = set()
    for summary in summaries:
        count += summary.count
        for kind in summary.types:
            seen.add(kind)
    kinds = [kind for kind in _TYPE_ORDER if kind in seen]
    kinds.extend(sorted(kind for kind in seen if kind not in _TYPE_ORDER))
    return RedactionSummary(count=count, types=tuple(kinds))
