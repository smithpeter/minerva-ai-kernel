from __future__ import annotations

import re

from .types import Decision, Observation


def propose_baseline_decision(observation: Observation) -> Decision:
    """Return a deterministic CPU-local decision for common failure shapes."""

    text = _combined_text(observation)
    runtime = observation.runtime

    if observation.exit_code == 0:
        return _decision(
            failure="command_succeeded",
            action="stop",
            confidence=0.96,
            evidence=["observed command exited with code 0"],
            reason="No failure signal was present in the bounded observation.",
        )

    if runtime.get("timed_out") is True or observation.exit_code == 124:
        return _decision(
            failure="command_timeout",
            action="check_logs",
            confidence=0.90,
            evidence=["runtime indicates the observed command timed out"],
            reason="Inspect bounded logs or runtime state before retrying.",
        )

    if runtime.get("command_found") is False or observation.exit_code == 127:
        return _decision(
            failure="command_not_found",
            action="check_command_exists",
            confidence=0.93,
            evidence=["runtime indicates the executable was not found"],
            reason="Verify the command is installed and available on PATH.",
        )

    if observation.exit_code == 126 or "permission denied" in text:
        return _decision(
            failure="permission_denied",
            action="check_permissions",
            confidence=0.88,
            evidence=["observation contains a permission denied signal"],
            reason="Check executable bits, file ownership, or service permissions.",
        )

    if _contains_any(
        text,
        (
            "modulenotfounderror",
            "importerror",
            "no module named",
            "cannot find module",
            "module not found",
            "package not found",
        ),
    ):
        return _decision(
            failure="missing_dependency",
            action="inspect_dependencies",
            confidence=0.89,
            evidence=["observation contains a missing dependency signal"],
            reason="Inspect dependency declarations and the active runtime environment.",
        )

    if _contains_any(
        text,
        (
            "could not resolve host",
            "name or service not known",
            "temporary failure in name resolution",
            "nodename nor servname provided",
            "dns",
        ),
    ):
        return _decision(
            failure="dns_resolution_failure",
            action="check_dns",
            confidence=0.86,
            evidence=["observation contains a DNS resolution signal"],
            reason="Check resolver configuration and the target hostname.",
        )

    if _contains_any(
        text,
        (
            "connection refused",
            "connection timed out",
            "network is unreachable",
            "failed to connect",
        ),
    ):
        return _decision(
            failure="network_connection_failure",
            action="check_network",
            confidence=0.82,
            evidence=["observation contains a network connection signal"],
            reason="Check network reachability and the target service endpoint.",
        )

    if _contains_any(
        text,
        (
            "jsondecodeerror",
            "invalid json",
            "expected value: line",
            "schema validation",
            "validationerror",
        ),
    ):
        return _decision(
            failure="schema_or_json_error",
            action="inspect_file",
            confidence=0.80,
            evidence=["observation contains a JSON or schema validation signal"],
            reason="Inspect the referenced input or artifact before retrying.",
        )

    if _contains_any(
        text,
        (
            "missing script:",
            "npm err!",
            "enoent: no such file or directory, open",
            "cannot find package.json",
        ),
    ):
        return _decision(
            failure="node_package_or_script_failure",
            action="inspect_dependencies",
            confidence=0.82,
            evidence=["observation contains an npm or package metadata signal"],
            reason="Inspect package metadata and scripts before retrying.",
        )

    if _contains_any(
        text,
        (
            "not a git repository",
            "fatal: ambiguous argument",
            "fatal: bad revision",
            "merge conflict",
        ),
    ):
        return _decision(
            failure="git_repository_failure",
            action="check_logs",
            confidence=0.81,
            evidence=["observation contains a git repository failure signal"],
            reason="Inspect the git error and repository state before retrying.",
        )

    if _contains_any(
        text,
        (
            "dockerfile",
            "failed to solve",
            "docker build",
            "container build",
            "no such image",
        ),
    ):
        return _decision(
            failure="container_build_failure",
            action="check_logs",
            confidence=0.80,
            evidence=["observation contains a container build failure signal"],
            reason="Inspect bounded build logs and referenced Dockerfile metadata.",
        )

    if _contains_any(
        text,
        (
            "address already in use",
            "eaddrinuse",
            "port is already allocated",
        ),
    ):
        return _decision(
            failure="port_in_use",
            action="check_port",
            confidence=0.82,
            evidence=["observation contains a port collision signal"],
            reason="Check which local service owns the target port.",
        )

    if _contains_any(text, ("traceback", "error:", "exception", "failed", "failure")):
        return _decision(
            failure="generic_runtime_failure",
            action="check_logs",
            confidence=0.74,
            evidence=["observation contains a generic runtime failure signal"],
            reason="Use bounded logs to identify the first concrete failure line.",
        )

    return _decision(
        failure="unknown_failure",
        action="check_logs",
        confidence=0.69,
        evidence=["observed command failed without a recognized signature"],
        reason="The deterministic baseline found no specific failure signature.",
    )


def _decision(
    *,
    failure: str,
    action: str,
    confidence: float,
    evidence: list[str],
    reason: str,
) -> Decision:
    return Decision(
        failure=failure,
        action=action,  # type: ignore[arg-type]
        confidence=confidence,
        risk="low",
        escalate=False,
        evidence=evidence,
        reason=reason,
    )


def _combined_text(observation: Observation) -> str:
    parts = [
        observation.command,
        observation.stdout_tail,
        observation.stderr_tail,
        " ".join(f"{key}={value}" for key, value in observation.runtime.items()),
    ]
    normalized = "\n".join(parts).lower()
    return re.sub(r"\s+", " ", normalized)


def _contains_any(value: str, needles: tuple[str, ...]) -> bool:
    return any(needle in value for needle in needles)
