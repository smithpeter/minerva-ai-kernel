from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from fnmatch import fnmatch
from pathlib import Path
from typing import Any, Callable, Sequence

from .policy import CREDENTIAL_PATTERNS, DESTRUCTIVE_COMMAND_PATTERNS
from .redaction import redact_value


MERGE_EVIDENCE_SCHEMA_VERSION = "merge_evidence.v0"
CHECK_TAIL_CHARS = 2000

DOC_SUFFIXES = {".md", ".rst", ".txt"}
DEPENDENCY_FILES = {
    "package-lock.json",
    "package.json",
    "pnpm-lock.yaml",
    "poetry.lock",
    "pyproject.toml",
    "requirements-dev.txt",
    "requirements.txt",
    "setup.cfg",
    "setup.py",
    "uv.lock",
}
SCHEMA_SUFFIXES = {".json", ".jsonl", ".yaml", ".yml", ".toml"}
RUNTIME_DIRS = ("minerva_kernel/", "scripts/")
TEST_DIRS = ("tests/",)
DOC_DIRS = ("docs/",)
EVAL_DIRS = ("eval/", "evals/", "corpus/")
CI_DIRS = (".github/", "action/")
PLANNING_DIRS = (".tasks/",)
SITE_DIRS = ("public-site/",)
CONTAINER_FILES = {"Dockerfile", "docker-compose.yml", "docker-compose.yaml"}
SECURITY_SENSITIVE_PATHS = (
    "policy.py",
    "executor.py",
    "redaction.py",
    "SECURITY.md",
)
POLICY_TEXT_EXEMPT_DIRS = (
    ".tasks/",
    "corpus/",
    "docs/",
    "eval/",
    "evals/",
    "tests/",
)
POLICY_TEXT_EXEMPT_FILES = {
    "README.md",
    "ROADMAP.md",
}


@dataclass(frozen=True)
class DiffEntry:
    status: str
    path: str
    previous_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = {"status": self.status, "path": self.path}
        if self.previous_path:
            payload["previous_path"] = self.previous_path
        return payload


@dataclass(frozen=True)
class SafeCheck:
    kind: str
    argv: tuple[str, ...]
    timeout_seconds: float = 120.0

    @property
    def command(self) -> str:
        return " ".join(self.argv)


@dataclass(frozen=True)
class SafeCheckResult:
    kind: str
    command: str
    exit_code: int
    stdout_tail: str
    stderr_tail: str

    @property
    def passed(self) -> bool:
        return self.exit_code == 0


def build_merge_evidence(
    diff_spec: str,
    *,
    repo_path: str | Path = ".",
    created_at: str | None = None,
    include_untracked: bool = False,
    run_checks: bool = False,
    check_runner: Callable[[SafeCheck, Path], SafeCheckResult] | None = None,
    exclude_patterns: Sequence[str] = (),
) -> dict[str, Any]:
    repo = Path(repo_path)
    entries = load_git_diff_entries(diff_spec, repo_path=repo)
    if include_untracked:
        entries = [*entries, *load_git_untracked_entries(repo_path=repo)]
    entries = _filter_excluded_entries(entries, exclude_patterns)
    added_lines = load_git_added_lines(
        diff_spec,
        repo_path=repo,
        exclude_patterns=exclude_patterns,
    )
    repository = _repository_name(repo)
    report = build_merge_evidence_from_entries(
        entries,
        diff_spec=diff_spec,
        repository=repository,
        created_at=created_at,
        added_lines=added_lines,
    )
    if run_checks:
        apply_verification_checks(report, repo_path=repo, check_runner=check_runner)
    return report


def build_merge_evidence_from_entries(
    entries: Sequence[DiffEntry],
    *,
    diff_spec: str,
    repository: str,
    created_at: str | None = None,
    added_lines: Sequence[str] = (),
) -> dict[str, Any]:
    safe_added_lines, added_line_secrets_detected = _redacted_added_lines(added_lines)
    changed_files = [entry.to_dict() for entry in entries]
    primary_areas = _primary_areas(entries)
    risk_level = _risk_level(
        entries,
        safe_added_lines,
        added_line_secrets_detected=added_line_secrets_detected,
    )
    policy = _policy_summary(
        entries,
        safe_added_lines,
        added_line_secrets_detected=added_line_secrets_detected,
    )
    merge_readiness = _merge_readiness(
        entries=entries,
        risk_level=risk_level,
        policy_decision=str(policy["decision"]),
    )

    verified = [
        {
            "kind": "diff_inspection",
            "status": "passed",
            "evidence": f"parsed {len(entries)} changed file(s) from git diff",
        }
    ]
    if primary_areas:
        verified.append(
            {
                "kind": "changed_file_classification",
                "status": "passed",
                "evidence": ", ".join(primary_areas),
            }
        )

    unverified = _unverified_items(entries, primary_areas)
    risks = _risks(entries, safe_added_lines, policy)
    recommended_next_steps = _recommended_next_steps(entries, primary_areas, policy)
    base, head = _split_diff_spec(diff_spec)

    return {
        "schema_version": MERGE_EVIDENCE_SCHEMA_VERSION,
        "subject": {
            "type": "git_diff",
            "base": base,
            "head": head,
            "diff": diff_spec,
            "repository": repository,
        },
        "summary": {
            "change_intent": _change_intent(primary_areas),
            "changed_files": len(entries),
            "primary_areas": primary_areas,
            "risk_level": risk_level,
            "merge_readiness": merge_readiness,
        },
        "changed_files": changed_files,
        "verified": verified,
        "unverified": unverified,
        "risks": risks,
        "policy": policy,
        "recommended_next_steps": recommended_next_steps,
        "audit": {
            "created_at": created_at or _utc_timestamp(),
            "generator": "minerva",
            "artifacts": [],
        },
    }


def render_merge_evidence_json(report: dict[str, Any]) -> str:
    return json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True) + "\n"


def load_merge_evidence(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("merge evidence JSON must be an object")
    if payload.get("schema_version") != MERGE_EVIDENCE_SCHEMA_VERSION:
        raise ValueError(
            "unsupported merge evidence schema_version: "
            f"{payload.get('schema_version')}"
        )
    return payload


def render_merge_evidence_markdown_from_file(path: str | Path) -> str:
    return render_merge_evidence_markdown(load_merge_evidence(path))


def render_merge_evidence_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    policy = report["policy"]
    changed_files = report.get("changed_files", [])
    lines = [
        "# Minerva Merge Evidence",
        "",
        f"Merge readiness: `{summary['merge_readiness']}`",
        f"Risk: `{summary['risk_level']}`",
        f"Changed files: `{summary['changed_files']}`",
        f"Primary areas: `{', '.join(summary['primary_areas']) or 'none'}`",
        "",
        "## Policy",
        "",
        f"- Decision: `{policy['decision']}`",
        f"- Dangerous actions detected: `{str(policy['dangerous_actions_detected']).lower()}`",
        f"- Secret access detected: `{str(policy['secret_access_detected']).lower()}`",
        "",
        "## Verified",
        "",
    ]
    lines.extend(_markdown_bullets(report["verified"], key="evidence"))
    lines.extend(["", "## Unverified", ""])
    lines.extend(_markdown_bullets(report["unverified"], key="reason"))
    lines.extend(["", "## Risks", ""])
    lines.extend(_risk_bullets(report["risks"]))
    lines.extend(["", "## Next Steps", ""])
    lines.extend(f"- {step}" for step in report["recommended_next_steps"])
    lines.extend(["", "## Changed Files", ""])
    if changed_files:
        for file_info in changed_files[:25]:
            status = file_info.get("status", "")
            path = file_info.get("path", "")
            lines.append(f"- `{status}` `{path}`")
        if len(changed_files) > 25:
            lines.append(f"- ... {len(changed_files) - 25} more file(s)")
    else:
        lines.append("- none")
    return "\n".join(lines) + "\n"


def render_merge_evidence(
    *,
    diff_spec: str,
    output_format: str,
    repo_path: str | Path = ".",
    include_untracked: bool = False,
    run_checks: bool = False,
    exclude_patterns: Sequence[str] = (),
) -> str:
    report = build_merge_evidence(
        diff_spec,
        repo_path=repo_path,
        include_untracked=include_untracked,
        run_checks=run_checks,
        exclude_patterns=exclude_patterns,
    )
    if output_format == "json":
        return render_merge_evidence_json(report)
    if output_format == "markdown":
        return render_merge_evidence_markdown(report)
    raise ValueError(f"unsupported output format: {output_format}")


def apply_verification_checks(
    report: dict[str, Any],
    *,
    repo_path: str | Path = ".",
    check_runner: Callable[[SafeCheck, Path], SafeCheckResult] | None = None,
) -> dict[str, Any]:
    repo = Path(repo_path)
    runner = check_runner or _run_safe_check
    checks = _selected_safe_checks(report)
    if not checks:
        return report

    failed: list[SafeCheckResult] = []
    executed_kinds: set[str] = set()
    for check in checks:
        result = runner(check, repo)
        executed_kinds.add(check.kind)
        report["verified"].append(_check_result_to_verified(result))
        if not result.passed:
            failed.append(result)

    _remove_unverified_for_executed_checks(report, executed_kinds)
    _remove_resolved_missing_test_risk(report, executed_kinds, failed)

    if failed:
        report["summary"]["merge_readiness"] = "blocked"
        report["summary"]["risk_level"] = "high"
        for result in failed:
            report["risks"].append(
                {
                    "id": "verification_check_failed",
                    "severity": "high",
                    "description": (
                        "Allowlisted verification check failed: "
                        f"{result.command}"
                    ),
                    "mitigation": (
                        "inspect bounded stdout/stderr and fix the failing check"
                    ),
                }
            )
    elif not report["unverified"] and report["policy"]["decision"] == "allowed":
        report["summary"]["merge_readiness"] = "ready"

    return report


def load_git_diff_entries(
    diff_spec: str,
    *,
    repo_path: str | Path = ".",
) -> list[DiffEntry]:
    completed = _git(["diff", "--name-status", diff_spec], repo_path=repo_path)
    entries: list[DiffEntry] = []
    for line in completed.stdout.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        status = parts[0]
        if status.startswith("R") or status.startswith("C"):
            if len(parts) >= 3:
                entries.append(DiffEntry(status=status, previous_path=parts[1], path=parts[2]))
            continue
        if len(parts) >= 2:
            entries.append(DiffEntry(status=status, path=parts[1]))
    return entries


def load_git_added_lines(
    diff_spec: str,
    *,
    repo_path: str | Path = ".",
    exclude_patterns: Sequence[str] = (),
) -> list[str]:
    completed = _git(["diff", "--unified=0", "--no-ext-diff", diff_spec], repo_path=repo_path)
    lines: list[str] = []
    include_current_file = True
    for line in completed.stdout.splitlines():
        if line.startswith("+++"):
            path = _diff_header_path(line)
            include_current_file = (
                path is None
                or (
                    not _matches_any(path, exclude_patterns)
                    and not _is_policy_text_exempt_path(path)
                )
            )
            continue
        if not line.startswith("+") or not include_current_file:
            continue
        lines.append(line[1:])
    return lines


def load_git_untracked_entries(
    *,
    repo_path: str | Path = ".",
) -> list[DiffEntry]:
    completed = _git(["ls-files", "--others", "--exclude-standard"], repo_path=repo_path)
    return [
        DiffEntry(status="?", path=line)
        for line in completed.stdout.splitlines()
        if line.strip()
    ]


def _filter_excluded_entries(
    entries: Sequence[DiffEntry],
    exclude_patterns: Sequence[str],
) -> list[DiffEntry]:
    if not exclude_patterns:
        return list(entries)
    return [
        entry
        for entry in entries
        if not _matches_any(entry.path, exclude_patterns)
        and (
            entry.previous_path is None
            or not _matches_any(entry.previous_path, exclude_patterns)
        )
    ]


def _diff_header_path(line: str) -> str | None:
    value = line[4:].strip()
    if value == "/dev/null":
        return None
    if value.startswith("b/"):
        return value[2:]
    return value or None


def _matches_any(path: str, patterns: Sequence[str]) -> bool:
    return any(fnmatch(path, pattern) for pattern in patterns)


def _is_policy_text_exempt_path(path: str) -> bool:
    return (
        path in POLICY_TEXT_EXEMPT_FILES
        or path.startswith(POLICY_TEXT_EXEMPT_DIRS)
        or Path(path).suffix.lower() in DOC_SUFFIXES
    )


def _selected_safe_checks(report: dict[str, Any]) -> list[SafeCheck]:
    areas = set(report["summary"].get("primary_areas", []))
    checks = [
        SafeCheck(
            kind="unit_tests",
            argv=("python3", "-m", "unittest", "discover", "-s", "tests"),
        ),
        SafeCheck(
            kind="verify_eval",
            argv=("python3", "-m", "minerva_kernel.verify_eval", "--format", "json"),
        ),
    ]
    if areas.intersection({"runtime", "security"}):
        checks.insert(
            0,
            SafeCheck(
                kind="compile",
                argv=("python3", "-m", "compileall", "minerva_kernel"),
            ),
        )
        checks.append(
            SafeCheck(
                kind="runtime_smoke",
                argv=("python3", "-m", "minerva_kernel.eval_smoke"),
            )
        )
    return _dedupe_checks(checks)


def _run_safe_check(check: SafeCheck, repo: Path) -> SafeCheckResult:
    try:
        completed = subprocess.run(
            list(check.argv),
            cwd=str(repo),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=check.timeout_seconds,
            check=False,
        )
        return SafeCheckResult(
            kind=check.kind,
            command=check.command,
            exit_code=completed.returncode,
            stdout_tail=_tail(completed.stdout or "", CHECK_TAIL_CHARS),
            stderr_tail=_tail(completed.stderr or "", CHECK_TAIL_CHARS),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return SafeCheckResult(
            kind=check.kind,
            command=check.command,
            exit_code=124 if isinstance(exc, subprocess.TimeoutExpired) else 127,
            stdout_tail="",
            stderr_tail=_tail(str(exc), CHECK_TAIL_CHARS),
        )


def _check_result_to_verified(result: SafeCheckResult) -> dict[str, Any]:
    return {
        "kind": result.kind,
        "command": result.command,
        "status": "passed" if result.passed else "failed",
        "exit_code": result.exit_code,
        "stdout_tail": result.stdout_tail,
        "stderr_tail": result.stderr_tail,
        "evidence": f"{result.command} exited {result.exit_code}",
    }


def _remove_unverified_for_executed_checks(
    report: dict[str, Any],
    executed_kinds: set[str],
) -> None:
    resolved = {"unit_tests", "runtime_smoke"}
    report["unverified"] = [
        item
        for item in report["unverified"]
        if item.get("kind") not in resolved.intersection(executed_kinds)
    ]


def _remove_resolved_missing_test_risk(
    report: dict[str, Any],
    executed_kinds: set[str],
    failed: Sequence[SafeCheckResult],
) -> None:
    if "unit_tests" not in executed_kinds or any(
        result.kind == "unit_tests" for result in failed
    ):
        return
    report["risks"] = [
        risk for risk in report["risks"] if risk.get("id") != "missing_tests"
    ]


def _dedupe_checks(checks: Sequence[SafeCheck]) -> list[SafeCheck]:
    seen: set[str] = set()
    result: list[SafeCheck] = []
    for check in checks:
        if check.kind in seen:
            continue
        seen.add(check.kind)
        result.append(check)
    return result


def _git(args: Sequence[str], *, repo_path: str | Path) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            ["git", *args],
            cwd=str(repo_path),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        raise ValueError(f"git {' '.join(args)} failed: {stderr or exc}") from exc


def _repository_name(repo_path: Path) -> str:
    try:
        completed = _git(["config", "--get", "remote.origin.url"], repo_path=repo_path)
    except ValueError:
        return repo_path.resolve().name
    remote = completed.stdout.strip()
    if not remote:
        return repo_path.resolve().name
    name = remote.rstrip("/").split("/")[-1]
    return name.removesuffix(".git") or repo_path.resolve().name


def _primary_areas(entries: Sequence[DiffEntry]) -> list[str]:
    areas: set[str] = set()
    for entry in entries:
        path = entry.path
        suffix = Path(path).suffix.lower()
        name = Path(path).name
        if path.startswith(DOC_DIRS) or suffix in DOC_SUFFIXES or name in {"README.md"}:
            areas.add("docs")
        if path.startswith(PLANNING_DIRS) or name in {"ROADMAP.md"}:
            areas.add("planning")
        if path.startswith(TEST_DIRS):
            areas.add("tests")
        if path.startswith(RUNTIME_DIRS):
            areas.add("runtime")
        if path.startswith(EVAL_DIRS):
            areas.add("eval")
        if path.startswith(CI_DIRS):
            areas.add("ci")
        if path.startswith(SITE_DIRS):
            areas.add("site")
        if name in CONTAINER_FILES:
            areas.add("container")
        if path.startswith("migrations/") or suffix == ".sql":
            areas.add("migration")
        if name in DEPENDENCY_FILES:
            areas.add("dependencies")
        if suffix in SCHEMA_SUFFIXES:
            areas.add("schema")
        if _is_security_sensitive_path(path):
            areas.add("security")
    return sorted(areas)


def _risk_level(
    entries: Sequence[DiffEntry],
    added_lines: Sequence[str],
    *,
    added_line_secrets_detected: bool = False,
) -> str:
    if not entries:
        return "unknown"
    paths = [entry.path for entry in entries]
    if _has_secret_signal(
        paths,
        added_line_secrets_detected=added_line_secrets_detected,
    ) or _has_dangerous_command(added_lines):
        return "high"
    areas = set(_primary_areas(entries))
    if areas.intersection(
        {"runtime", "security", "dependencies", "ci", "container", "migration"}
    ):
        return "medium"
    return "low"


def _merge_readiness(
    *,
    entries: Sequence[DiffEntry],
    risk_level: str,
    policy_decision: str,
) -> str:
    if policy_decision == "blocked":
        return "blocked"
    if not entries:
        return "unknown"
    if risk_level == "high":
        return "blocked"
    return "caution"


def _policy_summary(
    entries: Sequence[DiffEntry],
    added_lines: Sequence[str],
    *,
    added_line_secrets_detected: bool = False,
) -> dict[str, Any]:
    paths = [entry.path for entry in entries]
    dangerous = _has_dangerous_command(added_lines)
    secret = _has_secret_signal(
        paths,
        added_line_secrets_detected=added_line_secrets_detected,
    )
    decision = "blocked" if dangerous or secret else "allowed"
    return {
        "dangerous_actions_detected": dangerous,
        "writes_detected": bool(entries),
        "secret_access_detected": secret,
        "decision": decision,
    }


def _unverified_items(entries: Sequence[DiffEntry], primary_areas: Sequence[str]) -> list[dict[str, str]]:
    if not entries:
        return [
            {
                "kind": "diff_scope",
                "reason": "no changed files were found in the requested diff",
                "recommended_next_step": "confirm the diff range",
            }
        ]
    items = [
        {
            "kind": "unit_tests",
            "reason": "full unit tests were not run by verify --diff",
            "recommended_next_step": "python3 -m unittest discover -s tests",
        }
    ]
    areas = set(primary_areas)
    if areas.intersection({"runtime", "security"}):
        items.append(
            {
                "kind": "runtime_smoke",
                "reason": "runtime or security-sensitive files changed",
                "recommended_next_step": "python3 -m minerva_kernel.eval_smoke",
            }
        )
    if areas.intersection({"dependencies", "ci"}):
        items.append(
            {
                "kind": "integration_tests",
                "reason": "dependency or CI behavior may differ outside local diff inspection",
                "recommended_next_step": "run the GitHub Actions smoke workflow",
            }
        )
    if areas.intersection({"container", "migration"}):
        items.append(
            {
                "kind": "integration_tests",
                "reason": "container or migration changes need environment-level validation",
                "recommended_next_step": "run a targeted runtime smoke or migration replay",
            }
        )
    return items


def _risks(
    entries: Sequence[DiffEntry],
    added_lines: Sequence[str],
    policy: dict[str, Any],
) -> list[dict[str, str]]:
    risks: list[dict[str, str]] = []
    areas = set(_primary_areas(entries))
    if policy["secret_access_detected"]:
        risks.append(
            {
                "id": "secret_exposure",
                "severity": "high",
                "description": "The diff path or added lines contain credential-like signals.",
                "mitigation": "remove secrets and rerun redaction/policy checks",
            }
        )
    if policy["dangerous_actions_detected"]:
        risks.append(
            {
                "id": "dangerous_action",
                "severity": "high",
                "description": "The diff adds a destructive command pattern.",
                "mitigation": "replace with a reviewed bounded operation or explicit approval flow",
            }
        )
    if areas.intersection({"runtime", "security"}):
        risks.append(
            {
                "id": "runtime_behavior_change",
                "severity": "medium",
                "description": "Runtime or security-sensitive code changed.",
                "mitigation": "run compile, unit, policy, and eval smoke checks",
            }
        )
    if "dependencies" in areas:
        risks.append(
            {
                "id": "dependency_change",
                "severity": "medium",
                "description": "Dependency metadata changed.",
                "mitigation": "verify local install and CI dependency resolution",
            }
        )
    if "ci" in areas:
        risks.append(
            {
                "id": "ci_behavior_change",
                "severity": "medium",
                "description": "CI workflow or action behavior changed.",
                "mitigation": "run or inspect the affected workflow before merge",
            }
        )
    if "container" in areas:
        risks.append(
            {
                "id": "container_runtime_change",
                "severity": "medium",
                "description": "Container build or runtime metadata changed.",
                "mitigation": "run a targeted container build or smoke check",
            }
        )
    if "migration" in areas:
        risks.append(
            {
                "id": "migration_risk",
                "severity": "medium",
                "description": "Database or state migration files changed.",
                "mitigation": "run migration replay and rollback checks",
            }
        )
    if not risks:
        risks.append(
            {
                "id": "missing_tests",
                "severity": "low",
                "description": "Diff inspection alone does not prove behavior.",
                "mitigation": "run the recommended test command before merge",
            }
        )
    return risks


def _recommended_next_steps(
    entries: Sequence[DiffEntry],
    primary_areas: Sequence[str],
    policy: dict[str, Any],
) -> list[str]:
    if policy["decision"] == "blocked":
        return ["resolve blocked policy signals before running further verification"]
    if not entries:
        return ["confirm the diff range includes the intended changes"]
    steps = ["python3 -m unittest discover -s tests"]
    areas = set(primary_areas)
    if areas.intersection({"runtime", "security"}):
        steps.insert(0, "python3 -m compileall minerva_kernel")
        steps.append("python3 -m minerva_kernel.eval_smoke")
    if areas.intersection({"dependencies", "ci"}):
        steps.append(
            "python3 scripts/check-release-readiness.py --skip-external --install-backend auto"
        )
    if "container" in areas:
        steps.append("docker build .")
    if "migration" in areas:
        steps.append("run migration replay and rollback checks")
    if areas == {"docs"} or areas.issubset({"docs", "planning"}):
        steps.append("review docs for roadmap/schema consistency")
    return _dedupe(steps)


def _change_intent(primary_areas: Sequence[str]) -> str:
    if not primary_areas:
        return "No changed files detected."
    if set(primary_areas).issubset({"docs", "planning"}):
        return "Documentation and planning update."
    return "Code or configuration update requiring targeted verification."


def _split_diff_spec(diff_spec: str) -> tuple[str, str]:
    if "..." in diff_spec:
        base, head = diff_spec.split("...", 1)
        return base, head
    if ".." in diff_spec:
        base, head = diff_spec.split("..", 1)
        return base, head
    return diff_spec, ""


def _redacted_added_lines(added_lines: Sequence[str]) -> tuple[list[str], bool]:
    result = redact_value(list(added_lines))
    value = result.value
    if isinstance(value, list):
        return [str(item) for item in value], result.summary.count > 0
    return [], result.summary.count > 0


def _has_secret_signal(
    paths: Sequence[str],
    *,
    added_line_secrets_detected: bool = False,
) -> bool:
    path_text = "\n".join(paths).lower()
    if any(pattern in path_text for pattern in CREDENTIAL_PATTERNS):
        return True
    return added_line_secrets_detected


def _has_dangerous_command(added_lines: Sequence[str]) -> bool:
    text = _normalize_shell_text("\n".join(added_lines))
    return any(pattern in text for pattern in DESTRUCTIVE_COMMAND_PATTERNS)


def _normalize_shell_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower())


def _is_security_sensitive_path(path: str) -> bool:
    return any(part in path for part in SECURITY_SENSITIVE_PATHS)


def _markdown_bullets(items: Sequence[dict[str, Any]], *, key: str) -> list[str]:
    if not items:
        return ["- none"]
    return [f"- `{item.get('kind', 'unknown')}`: {item.get(key, '')}" for item in items]


def _risk_bullets(items: Sequence[dict[str, Any]]) -> list[str]:
    if not items:
        return ["- none"]
    return [
        f"- `{item.get('severity', 'unknown')}` `{item.get('id', 'risk')}`: "
        f"{item.get('description', '')}"
        for item in items
    ]


def _dedupe(values: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _tail(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[-limit:]


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
