#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from minerva_kernel.redaction import redact_text

DEFAULT_OUTPUT = ROOT / "corpus" / "real_world_v0" / "entries.jsonl"
DEFAULT_CACHE_DIR = Path.home() / ".cache" / "gh"

LICENSE_NOTES = {
    "pytest-dev/pytest": (
        "pytest-dev/pytest is MIT licensed; source: "
        "https://github.com/pytest-dev/pytest/blob/main/LICENSE."
    ),
    "encode/httpx": (
        "encode/httpx is BSD-3-Clause licensed; source: "
        "https://github.com/encode/httpx/blob/master/LICENSE.md."
    ),
    "fastapi/fastapi": (
        "fastapi/fastapi is MIT licensed; source: "
        "https://github.com/fastapi/fastapi/blob/master/LICENSE."
    ),
}


@dataclass(frozen=True)
class SourceRun:
    repo: str
    run_id: str
    expected_failure_label: str
    expected_action: str

    @property
    def run_url(self) -> str:
        return f"https://github.com/{self.repo}/actions/runs/{self.run_id}"


DEFAULT_SOURCES = (
    SourceRun("pytest-dev/pytest", "25622547871", "github_actions_permission_denied", "check_permissions"),
    SourceRun("pytest-dev/pytest", "25622153209", "github_actions_permission_denied", "check_permissions"),
    SourceRun("pytest-dev/pytest", "25615980901", "doc_link_check_failure", "check_network"),
    SourceRun("pytest-dev/pytest", "25602656139", "github_actions_permission_denied", "check_permissions"),
    SourceRun("pytest-dev/pytest", "25600062604", "dependabot_update_failure", "inspect_dependencies"),
    SourceRun("pytest-dev/pytest", "25585028060", "dependabot_update_failure", "inspect_dependencies"),
    SourceRun("pytest-dev/pytest", "25584931214", "dependabot_update_failure", "inspect_dependencies"),
    SourceRun("pytest-dev/pytest", "25566387126", "pytest_test_failure", "check_logs"),
    SourceRun("pytest-dev/pytest", "25452031429", "dependabot_update_failure", "inspect_dependencies"),
    SourceRun("pytest-dev/pytest", "25374939541", "pytest_test_failure", "check_logs"),
    SourceRun("pytest-dev/pytest", "25266041103", "doc_link_check_failure", "check_network"),
    SourceRun("pytest-dev/pytest", "25104921521", "pytest_test_failure", "check_logs"),
    SourceRun("pytest-dev/pytest", "24944556848", "doc_link_check_failure", "check_network"),
    SourceRun("pytest-dev/pytest", "24853110678", "pytest_test_failure", "check_logs"),
    SourceRun("pytest-dev/pytest", "24807672143", "pytest_test_failure", "check_logs"),
    SourceRun("pytest-dev/pytest", "24617503320", "doc_link_check_failure", "check_network"),
    SourceRun("pytest-dev/pytest", "24605215625", "pytest_test_failure", "check_logs"),
    SourceRun("encode/httpx", "22547825202", "httpx_test_failure", "check_logs"),
    SourceRun("encode/httpx", "22379030162", "httpx_test_failure", "check_logs"),
    SourceRun("encode/httpx", "22368072496", "httpx_test_failure", "check_logs"),
    SourceRun("encode/httpx", "22367742645", "httpx_test_failure", "check_logs"),
    SourceRun("encode/httpx", "22367610318", "httpx_test_failure", "check_logs"),
    SourceRun("encode/httpx", "22366275831", "httpx_test_failure", "check_logs"),
    SourceRun("encode/httpx", "22365864207", "httpx_test_failure", "check_logs"),
    SourceRun("encode/httpx", "22365804838", "httpx_test_failure", "check_logs"),
    SourceRun("encode/httpx", "22365498386", "httpx_test_failure", "check_logs"),
    SourceRun("encode/httpx", "22364859524", "httpx_test_failure", "check_logs"),
    SourceRun("encode/httpx", "22364740215", "httpx_test_failure", "check_logs"),
    SourceRun("encode/httpx", "22364576936", "httpx_test_failure", "check_logs"),
    SourceRun("encode/httpx", "22364449468", "httpx_test_failure", "check_logs"),
    SourceRun("encode/httpx", "22354219645", "httpx_test_failure", "check_logs"),
    SourceRun("encode/httpx", "22353570387", "httpx_test_failure", "check_logs"),
    SourceRun("encode/httpx", "22353131733", "httpx_test_failure", "check_logs"),
    SourceRun("encode/httpx", "22352954292", "httpx_test_failure", "check_logs"),
    SourceRun("fastapi/fastapi", "25619848895", "github_label_check_failure", "check_logs"),
    SourceRun("fastapi/fastapi", "25619821582", "pre_commit_failure", "check_logs"),
    SourceRun("fastapi/fastapi", "25619821124", "github_label_check_failure", "check_logs"),
    SourceRun("fastapi/fastapi", "25619809286", "github_label_check_failure", "check_logs"),
    SourceRun("fastapi/fastapi", "25619790656", "pre_commit_failure", "check_logs"),
    SourceRun("fastapi/fastapi", "25619790514", "github_label_check_failure", "check_logs"),
    SourceRun("fastapi/fastapi", "25619592601", "github_label_check_failure", "check_logs"),
    SourceRun("fastapi/fastapi", "25619592658", "pre_commit_failure", "check_logs"),
    SourceRun("fastapi/fastapi", "25619592654", "coverage_combine_failure", "check_logs"),
    SourceRun("fastapi/fastapi", "25603630572", "github_label_check_failure", "check_logs"),
    SourceRun("fastapi/fastapi", "25603630568", "coverage_combine_failure", "check_logs"),
    SourceRun("fastapi/fastapi", "25596681881", "coverage_upload_failure", "check_logs"),
    SourceRun("fastapi/fastapi", "25568018366", "github_actions_permission_denied", "check_permissions"),
    SourceRun("fastapi/fastapi", "25565630777", "dependabot_update_failure", "inspect_dependencies"),
    SourceRun("fastapi/fastapi", "25553659560", "coverage_upload_failure", "check_logs"),
    SourceRun("fastapi/fastapi", "25450410834", "coverage_upload_failure", "check_logs"),
)

ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")
EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
POSIX_PRIVATE_PATH_RE = re.compile(r"(?<![\w.-])/(?:Users|home)/[^\s:'\"]+")
WINDOWS_USER_PATH_RE = re.compile(r"\b[A-Za-z]:\\Users\\[^\s:'\"]+")
LONG_HEX_RE = re.compile(r"\b[a-f0-9]{32,64}\b", re.IGNORECASE)
UUID_RE = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
    re.IGNORECASE,
)
CREDENTIAL_NAME_RE = re.compile(
    r"\b[A-Z0-9_]*(?:TOKEN|API[_-]?KEY|SECRET)[A-Z0-9_]*\b",
    re.IGNORECASE,
)

MARKERS = (
    "##[error]",
    "error:",
    "failed",
    "failure",
    "traceback",
    "assertionerror",
    "resource not accessible",
    "process completed with exit code",
    "dependabot encountered",
    "the updater encountered",
    "some of the required",
    "linkcheck",
    "broken",
    "would reformat",
    "coverage",
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build the checked-in real_world_v0 corpus from public GitHub Actions runs."
    )
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE_DIR)
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Use cached GitHub CLI run-log zips only; do not invoke gh.",
    )
    args = parser.parse_args()

    entries = build_entries(cache_dir=args.cache_dir, offline=args.offline)
    write_jsonl(entries, args.out)
    print(f"Wrote {len(entries)} real-world corpus entries to {args.out}")


def build_entries(cache_dir: Path = DEFAULT_CACHE_DIR, offline: bool = False) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for index, source in enumerate(DEFAULT_SOURCES, 1):
        log_zip = cached_run_log(cache_dir, source)
        if log_zip is None and not offline:
            fetch_run_log(source)
            log_zip = cached_run_log(cache_dir, source)
        if log_zip is None:
            raise FileNotFoundError(
                f"missing cached log zip for {source.run_url}; run without --offline first"
            )

        raw_log = extract_failure_log(log_zip, source)
        entry = {
            "id": f"real-world-v0-{index:03d}",
            "repo": source.repo,
            "run_url": source.run_url,
            "raw_log_redacted": redact_log(raw_log),
            "expected_failure_label": source.expected_failure_label,
            "expected_action": source.expected_action,
            "license_note": LICENSE_NOTES[source.repo],
        }
        entries.append(entry)
    return entries


def cached_run_log(cache_dir: Path, source: SourceRun) -> Path | None:
    matches = sorted(cache_dir.glob(f"run-log-{source.run_id}-*.zip"))
    return matches[-1] if matches else None


def fetch_run_log(source: SourceRun) -> None:
    subprocess.run(
        ["gh", "run", "view", source.run_id, "--repo", source.repo, "--log-failed"],
        check=True,
    )


def extract_failure_log(log_zip: Path, source: SourceRun) -> str:
    with ZipFile(log_zip) as archive:
        names = [
            name
            for name in archive.namelist()
            if name.endswith(".txt") and not name.endswith("/system.txt")
        ]
        if not names:
            raise ValueError(f"{log_zip} contains no job log text files")

        scored_logs: list[tuple[int, str, str]] = []
        for name in names:
            text = archive.read(name).decode("utf-8", errors="replace")
            score = score_log(text, name, source)
            scored_logs.append((score, name, text))

    scored_logs.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return excerpt(scored_logs[0][2])


def score_log(text: str, name: str, source: SourceRun) -> int:
    lowered = text.lower()
    lowered_name = name.lower()
    score = sum(lowered.count(marker) for marker in MARKERS)

    label = source.expected_failure_label
    if label == "github_actions_permission_denied":
        if "resource not accessible" in lowered or "http 403" in lowered:
            score += 200
        if "cleanup" in lowered_name:
            score += 50
    elif label == "doc_link_check_failure":
        if "broken link" in lowered or "linkcheck" in lowered:
            score += 200
    elif label == "dependabot_update_failure":
        if "dependabot encountered" in lowered or "the updater encountered" in lowered:
            score += 200
    elif label == "pre_commit_failure":
        if "pre-commit" in lowered_name:
            score += 100
        if "would reformat" in lowered or "failed" in lowered:
            score += 75
    elif label == "github_label_check_failure":
        if "check-labels" in lowered_name or "labels" in lowered_name:
            score += 150
    elif label == "coverage_combine_failure":
        if "coverage-combine" in lowered_name:
            score += 150
    elif label == "coverage_upload_failure":
        if "smokeshow" in lowered_name:
            score += 150
    elif label in {"pytest_test_failure", "httpx_test_failure"}:
        if "failed" in lowered or "traceback" in lowered or "assertionerror" in lowered:
            score += 100
        if "alls-green" in lowered_name or lowered_name.startswith(("0_check", "check")):
            score -= 100

    if "alls-green" in lowered_name or lowered_name.startswith(("0_check", "check")):
        score -= 6
    if "system.txt" in lowered_name:
        score -= 100
    return score


def excerpt(text: str, max_lines: int = 90) -> str:
    lines = text.splitlines()
    if len(lines) <= max_lines:
        return "\n".join(lines)

    marker_indexes = [
        index
        for index, line in enumerate(lines)
        if any(marker in line.lower() for marker in MARKERS)
    ]
    center = marker_indexes[-1] if marker_indexes else len(lines) - 1
    start = max(0, center - max_lines + 1)
    end = min(len(lines), start + max_lines)
    return "\n".join(lines[start:end])


def redact_log(text: str) -> str:
    cleaned = text.replace("\ufeff", "")
    cleaned = ANSI_RE.sub("", cleaned)
    cleaned = EMAIL_RE.sub("[REDACTED:EMAIL]", cleaned)
    cleaned = POSIX_PRIVATE_PATH_RE.sub("[REDACTED:PATH]", cleaned)
    cleaned = WINDOWS_USER_PATH_RE.sub("[REDACTED:PATH]", cleaned)
    cleaned = UUID_RE.sub("[REDACTED:ID]", cleaned)
    cleaned = LONG_HEX_RE.sub("[REDACTED:HEX]", cleaned)
    cleaned = redact_text(cleaned).value
    cleaned = CREDENTIAL_NAME_RE.sub("[REDACTED:CREDENTIAL_NAME]", cleaned)
    return cleaned.strip()


def write_jsonl(entries: list[dict[str, str]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(entry, sort_keys=True, ensure_ascii=True) for entry in entries]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
