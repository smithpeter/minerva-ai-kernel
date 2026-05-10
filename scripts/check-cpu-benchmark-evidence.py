#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


SUMMARY_SCHEMA_VERSION = "minerva.cpu_model_benchmark_gate.v0"
ARTIFACT_SCHEMA_VERSION = "minerva.cpu_model_eval_artifact.v0"
REPORT_SCHEMA_VERSION = "minerva.cpu_model_eval_report.v0"
REAL_BENCHMARK_STATUS = "real_local_benchmark"


def validate_benchmark_artifact(path: str | Path) -> dict[str, Any]:
    artifact_path = Path(path)
    artifact = _load_object(artifact_path)
    errors: list[str] = []

    _require_equal(artifact, "schema_version", ARTIFACT_SCHEMA_VERSION, errors)
    _require_equal(artifact, "artifact_status", REAL_BENCHMARK_STATUS, errors)
    _require_equal(artifact, "benchmark_claim", True, errors)
    _require_equal(artifact, "fixture_report", False, errors)
    _require_equal(artifact, "model_weights_shipped_by_minerva", False, errors)
    _require_equal(artifact, "models_downloaded_by_artifact", False, errors)

    evidence = artifact.get("evidence_requirements")
    if not isinstance(evidence, dict):
        errors.append("evidence_requirements must be an object")
        evidence = {}
    _require_equal(evidence, "gpu_used", False, errors)
    _require_equal(evidence, "remote_models_used", False, errors)
    minimum_case_count = evidence.get("minimum_case_count", 0)
    if not isinstance(minimum_case_count, int) or minimum_case_count <= 0:
        errors.append("evidence_requirements.minimum_case_count must be positive")
        minimum_case_count = 0
    required_metrics = evidence.get("required_metrics", [])
    if isinstance(required_metrics, str) or not isinstance(required_metrics, list):
        errors.append("evidence_requirements.required_metrics must be a list")
        required_metrics = []

    report = artifact.get("report")
    if not isinstance(report, dict):
        errors.append("report must embed a cpu_model_eval_report.v0 object")
        report = {}
    _require_equal(report, "schema_version", REPORT_SCHEMA_VERSION, errors)
    if report.get("decision") not in {"promote", "retest", "reject"}:
        errors.append("report.decision must be promote, retest, or reject")

    corpus = report.get("corpus", {})
    if not isinstance(corpus, dict):
        errors.append("report.corpus must be an object")
        corpus = {}
    case_count = corpus.get("case_count", 0)
    if not isinstance(case_count, int) or case_count < minimum_case_count:
        errors.append("report.corpus.case_count is below minimum_case_count")

    minimum_path = report.get("minimum_path", {})
    if not isinstance(minimum_path, dict):
        errors.append("report.minimum_path must be an object")
        minimum_path = {}
    _require_equal(minimum_path, "gpu_used", False, errors)
    _require_equal(minimum_path, "remote_models_used", False, errors)
    _require_equal(minimum_path, "model_weights_shipped_by_minerva", False, errors)

    candidate = report.get("candidate", {})
    if not isinstance(candidate, dict):
        errors.append("report.candidate must be an object")
        candidate = {}
    if str(candidate.get("device", "")).lower() != "cpu":
        errors.append("report.candidate.device must be cpu")
    if str(candidate.get("runtime", "")).lower() == "fixture":
        errors.append("report.candidate.runtime must not be fixture")

    metrics = report.get("metrics", {})
    if not isinstance(metrics, dict):
        errors.append("report.metrics must be an object")
        metrics = {}
    for metric in required_metrics:
        if metric not in metrics:
            errors.append(f"report.metrics missing required metric: {metric}")

    return {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "artifact_path": str(artifact_path),
        "ready": not errors,
        "errors": errors,
        "candidate": artifact.get("registry_candidate_id", ""),
        "report_decision": report.get("decision", ""),
        "case_count": case_count if isinstance(case_count, int) else 0,
    }


def _load_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("artifact root must be a JSON object")
    return payload


def _require_equal(
    payload: dict[str, Any],
    field: str,
    expected: Any,
    errors: list[str],
) -> None:
    if payload.get(field) != expected:
        errors.append(f"{field} must be {expected!r}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate real local CPU model benchmark evidence.",
    )
    parser.add_argument("path")
    args = parser.parse_args(argv)

    try:
        summary = validate_benchmark_artifact(args.path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"CPU benchmark evidence check failed: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(summary, ensure_ascii=True, indent=2, sort_keys=True))
    return 0 if summary["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
