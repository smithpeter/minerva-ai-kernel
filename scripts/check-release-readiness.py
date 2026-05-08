#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import html.parser
import json
import os
import re
import shutil
import socket
import ssl
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


DEFAULT_DOMAIN = "minervakernel.com"
DEFAULT_REPO = "smithpeter/minerva-ai-kernel"
MAX_DETAIL_CHARS = 220
MAX_DETAILS_PER_CHECK = 8
MAX_LIST_ITEMS = 5

SECRET_PATTERNS = (
    re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"(?i)\b(token|secret|password|api[_-]?key)=\S+"),
    re.compile(r"(?i)\b(authorization:\s*bearer\s+)\S+"),
)


@dataclass(frozen=True)
class CheckResult:
    name: str
    status: str
    verified_by: str
    requires: str
    details: tuple[str, ...]


class TitleParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._in_title = False
        self.parts: list[str] = []

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        if tag.lower() == "title":
            self._in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.parts.append(data)

    @property
    def title(self) -> str:
        return bounded_text(" ".join(self.parts).strip() or "<none>", 120)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    timeout = max(args.timeout, 1.0)
    skip_github = args.skip_external or args.skip_github_actions
    skip_domain = args.skip_external or args.skip_domain

    context: dict[str, str] = {
        "timestamp_utc": dt.datetime.now(dt.UTC)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
        "domain": args.domain,
    }

    local = check_local_checkout(args.repo)
    context["repository"] = detail_value(local, "repository") or args.repo or DEFAULT_REPO
    context["commit"] = detail_value(local, "commit") or "<unknown>"

    results = [
        local,
        check_github_actions(
            repo=context["repository"],
            commit=context["commit"],
            timeout=timeout,
            skip=skip_github,
        ),
        check_dns(args.domain, timeout=timeout, skip=skip_domain),
        check_tls(args.domain, timeout=timeout, skip=skip_domain),
        check_https(args.domain, timeout=timeout, skip=skip_domain),
        check_content_review(args.content_reviewed, skip=skip_domain),
    ]

    exit_code = readiness_exit_code(results)
    print(format_report(context, results, exit_code))
    return exit_code


def parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check GitHub Actions and minervakernel.com release readiness "
            "without mutating external systems or printing credentials."
        )
    )
    parser.add_argument(
        "--repo",
        default=None,
        help=f"GitHub repository in owner/name form. Defaults to origin or {DEFAULT_REPO}.",
    )
    parser.add_argument(
        "--domain",
        default=DEFAULT_DOMAIN,
        help=f"Domain to verify. Defaults to {DEFAULT_DOMAIN}.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="Per-network-check timeout in seconds.",
    )
    parser.add_argument(
        "--skip-external",
        action="store_true",
        help="Skip GitHub and domain network checks; useful for local dry runs.",
    )
    parser.add_argument(
        "--skip-github-actions",
        action="store_true",
        help="Skip the GitHub Actions lookup only.",
    )
    parser.add_argument(
        "--skip-domain",
        action="store_true",
        help="Skip DNS, TLS, and HTTPS checks only.",
    )
    parser.add_argument(
        "--content-reviewed",
        default="",
        metavar="NOTE",
        help=(
            "Release-owner note confirming the HTTPS page is the intended "
            "public Minerva surface."
        ),
    )
    return parser.parse_args(argv)


def check_local_checkout(repo_arg: str | None) -> CheckResult:
    root = run_git(("rev-parse", "--show-toplevel"))
    commit = run_git(("rev-parse", "HEAD"))
    branch = run_git(("rev-parse", "--abbrev-ref", "HEAD"))
    remote = run_git(("remote", "get-url", "origin"))

    errors = [
        command_error("git rev-parse --show-toplevel", root),
        command_error("git rev-parse HEAD", commit),
        command_error("git rev-parse --abbrev-ref HEAD", branch),
    ]
    errors = [error for error in errors if error]
    if errors:
        return result(
            "local_checkout",
            "fail",
            "git",
            "local checkout",
            errors,
        )

    repo = repo_arg or repo_from_remote(remote.stdout.strip()) or DEFAULT_REPO
    root_path = Path(root.stdout.strip())
    details = [
        f"repo_root_basename={root_path.name}",
        f"commit={commit.stdout.strip()}",
        f"branch={branch.stdout.strip()}",
        f"repository={repo}",
    ]
    return result("local_checkout", "pass", "git", "local checkout", details)


def check_github_actions(
    *, repo: str, commit: str, timeout: float, skip: bool
) -> CheckResult:
    if skip:
        return result(
            "github_actions",
            "skipped",
            "not run",
            "network and GitHub access",
            ["skipped by --skip-external or --skip-github-actions"],
        )
    if not commit or commit == "<unknown>":
        return result(
            "github_actions",
            "unverified",
            "gh api",
            "network and GitHub access",
            ["current commit is unknown; cannot query workflow runs"],
        )
    if shutil.which("gh") is None:
        return result(
            "github_actions",
            "unverified",
            "gh api",
            "network, gh CLI, and repository access",
            [
                "gh CLI not found; use the GitHub Actions UI and record the run URL",
                f"commit={commit}",
            ],
        )

    completed = run_command(
        (
            "gh",
            "api",
            "--method",
            "GET",
            f"repos/{repo}/actions/runs",
            "-f",
            f"head_sha={commit}",
            "-f",
            "per_page=10",
        ),
        timeout=timeout,
        env_extra={"GH_PROMPT_DISABLED": "1", "GH_NO_UPDATE_NOTIFIER": "1"},
    )
    if completed.returncode != 0:
        return result(
            "github_actions",
            "unverified",
            "gh api",
            "network, gh CLI, and repository access",
            [
                command_error("gh api actions/runs", completed)
                or "gh api returned a non-zero exit code",
                f"commit={commit}",
            ],
        )

    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return result(
            "github_actions",
            "unverified",
            "gh api",
            "network, gh CLI, and repository access",
            ["gh api did not return JSON workflow data", f"commit={commit}"],
        )

    runs = payload.get("workflow_runs", [])
    return github_actions_result_from_runs(runs, commit=commit)


def github_actions_result_from_runs(
    runs: object, *, commit: str
) -> CheckResult:
    if not isinstance(runs, list) or not runs:
        return result(
            "github_actions",
            "unverified",
            "GitHub Actions API",
            "network and repository access",
            [f"no workflow runs returned for commit={commit}"],
        )

    run_details = summarize_workflow_runs(runs)
    failed = [
        run
        for run in runs
        if run.get("status") != "completed" or run.get("conclusion") != "success"
    ]
    status = "fail" if failed else "pass"
    details = [f"runs_returned={len(runs)}", *run_details]
    if failed:
        details.append("all returned runs must be completed with conclusion=success")
    return result(
        "github_actions",
        status,
        "GitHub Actions API",
        "network and repository access",
        details,
    )


def check_dns(domain: str, *, timeout: float, skip: bool) -> CheckResult:
    if skip:
        return result(
            "domain_dns",
            "skipped",
            "not run",
            "public DNS",
            ["skipped by --skip-external or --skip-domain"],
        )

    details: list[str] = []
    addresses: list[str] = []
    old_timeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(timeout)
    try:
        infos = socket.getaddrinfo(domain, 443, type=socket.SOCK_STREAM)
        addresses = sorted({info[4][0] for info in infos})
    except OSError as exc:
        details.append(f"socket resolver failed: {bounded_text(type(exc).__name__)}")
    finally:
        socket.setdefaulttimeout(old_timeout)

    if addresses:
        details.append("addresses=" + ", ".join(addresses[:MAX_LIST_ITEMS]))
    details.extend(dig_details(domain, timeout=timeout))
    status = "pass" if addresses else "fail"
    if not details:
        details.append("no A or AAAA address resolved")
    return result("domain_dns", status, "system resolver", "public DNS", details)


def check_tls(domain: str, *, timeout: float, skip: bool) -> CheckResult:
    if skip:
        return result(
            "domain_tls",
            "skipped",
            "not run",
            "network and public CA trust",
            ["skipped by --skip-external or --skip-domain"],
        )

    try:
        context = ssl.create_default_context()
        with socket.create_connection((domain, 443), timeout=timeout) as raw:
            with context.wrap_socket(raw, server_hostname=domain) as tls:
                cert = tls.getpeercert()
    except (OSError, ssl.SSLError) as exc:
        return result(
            "domain_tls",
            "fail",
            "Python ssl",
            "network and public CA trust",
            [f"TLS validation failed: {bounded_text(type(exc).__name__)}"],
        )

    details = [
        "subject=" + certificate_name(cert.get("subject", ())),
        "issuer=" + certificate_name(cert.get("issuer", ())),
        "not_after=" + bounded_text(str(cert.get("notAfter", "<unknown>"))),
    ]
    sans = [
        value
        for kind, value in cert.get("subjectAltName", ())
        if str(kind).lower() == "dns"
    ]
    if sans:
        details.append("dns_san=" + ", ".join(sans[:MAX_LIST_ITEMS]))
    return result("domain_tls", "pass", "Python ssl", "network and public CA trust", details)


def check_https(domain: str, *, timeout: float, skip: bool) -> CheckResult:
    if skip:
        return result(
            "domain_https",
            "skipped",
            "not run",
            "network and HTTPS endpoint",
            ["skipped by --skip-external or --skip-domain"],
        )

    url = f"https://{domain}/"
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "minerva-release-readiness/1.0",
            "Accept": "text/html,application/xhtml+xml,application/json;q=0.8,*/*;q=0.5",
            "Accept-Encoding": "identity",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status_code = int(response.status)
            final_url = response.geturl()
            content_type = response.headers.get("content-type", "<unknown>")
            body = response.read(65536)
    except urllib.error.HTTPError as exc:
        return result(
            "domain_https",
            "fail",
            "Python urllib",
            "network and HTTPS endpoint",
            [f"HTTP status={exc.code}", f"url={url}"],
        )
    except (OSError, urllib.error.URLError) as exc:
        return result(
            "domain_https",
            "fail",
            "Python urllib",
            "network and HTTPS endpoint",
            [f"HTTPS request failed: {bounded_text(type(exc).__name__)}"],
        )

    parsed = urllib.parse.urlparse(final_url)
    title = html_title(body, content_type)
    details = [
        f"status={status_code}",
        f"final_url={bounded_text(final_url)}",
        f"final_host={bounded_text(parsed.netloc or '<unknown>')}",
        f"content_type={bounded_text(content_type)}",
        f"title={title}",
        "content_review=manual release-owner confirmation still required",
    ]
    status = "pass" if 200 <= status_code < 400 and parsed.scheme == "https" else "fail"
    return result(
        "domain_https",
        status,
        "Python urllib",
        "network and HTTPS endpoint",
        details,
    )


def check_content_review(note: str, *, skip: bool) -> CheckResult:
    if skip:
        return result(
            "https_content_review",
            "skipped",
            "not run",
            "human review of public page",
            ["skipped by --skip-external or --skip-domain"],
        )
    if note.strip():
        return result(
            "https_content_review",
            "pass",
            "release owner",
            "human review of public page",
            [f"review_note={bounded_text(note.strip())}"],
        )
    return result(
        "https_content_review",
        "manual",
        "release owner",
        "human review of public page",
        [
            "verify HTTPS page is the intended Minerva public surface",
            "rerun with --content-reviewed NOTE to record the confirmation",
        ],
    )


def summarize_workflow_runs(runs: Iterable[Mapping[str, Any]]) -> list[str]:
    details = []
    for run in list(runs)[:MAX_LIST_ITEMS]:
        name = bounded_text(str(run.get("name") or run.get("workflowName") or "<unnamed>"), 80)
        status = bounded_text(str(run.get("status", "<unknown>")), 40)
        conclusion = bounded_text(str(run.get("conclusion", "<pending>")), 40)
        url = bounded_text(str(run.get("html_url", "<no url>")), 120)
        updated = bounded_text(str(run.get("updated_at", "<unknown>")), 40)
        details.append(
            f"run={name} status={status} conclusion={conclusion} updated={updated} url={url}"
        )
    return details


def dig_details(domain: str, *, timeout: float) -> list[str]:
    if shutil.which("dig") is None:
        return ["dig=unavailable; socket resolver used"]

    details: list[str] = []
    for record_type in ("A", "AAAA", "CNAME", "NS"):
        completed = run_command(
            ("dig", "+short", record_type, domain),
            timeout=min(timeout, 5.0),
        )
        if completed.returncode != 0:
            details.append(f"dig_{record_type}=unverified")
            continue
        records = [
            bounded_text(line.strip(), 80)
            for line in completed.stdout.splitlines()
            if line.strip()
        ]
        if records:
            details.append(f"dig_{record_type}=" + ", ".join(records[:MAX_LIST_ITEMS]))
    return details


def html_title(body: bytes, content_type: str) -> str:
    charset = "utf-8"
    match = re.search(r"charset=([^;\s]+)", content_type, flags=re.IGNORECASE)
    if match:
        charset = match.group(1).strip("\"'")
    try:
        text = body.decode(charset, errors="replace")
    except LookupError:
        text = body.decode("utf-8", errors="replace")
    parser = TitleParser()
    parser.feed(text)
    return parser.title


def certificate_name(value: object) -> str:
    parts: list[str] = []
    if isinstance(value, tuple):
        for item in value:
            if isinstance(item, tuple):
                for pair in item:
                    if (
                        isinstance(pair, tuple)
                        and len(pair) == 2
                        and pair[0] in {"commonName", "organizationName"}
                    ):
                        parts.append(str(pair[1]))
    return bounded_text(", ".join(parts) or "<unknown>", 160)


def run_git(args: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return run_command(("git", *args), timeout=10.0)


def run_command(
    args: Sequence[str],
    *,
    timeout: float,
    env_extra: Mapping[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)
    try:
        return subprocess.run(
            list(args),
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
            env=env,
        )
    except subprocess.TimeoutExpired as exc:
        return subprocess.CompletedProcess(
            list(args),
            124,
            stdout=bounded_text(exc.stdout or ""),
            stderr=f"timeout after {timeout:g}s",
        )


def command_error(
    label: str, completed: subprocess.CompletedProcess[str]
) -> str:
    if completed.returncode == 0:
        return ""
    message = first_nonempty_line(completed.stderr) or first_nonempty_line(
        completed.stdout
    )
    if not message:
        message = f"exit_code={completed.returncode}"
    return f"{label}: {bounded_text(message)}"


def first_nonempty_line(value: str | bytes | None) -> str:
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="replace")
    for line in str(value or "").splitlines():
        if line.strip():
            return line.strip()
    return ""


def repo_from_remote(remote: str) -> str:
    remote = remote.strip()
    patterns = (
        r"github\.com[:/](?P<repo>[^/\s]+/[^/\s]+?)(?:\.git)?$",
        r"^https?://github\.com/(?P<repo>[^/\s]+/[^/\s]+?)(?:\.git)?$",
    )
    for pattern in patterns:
        match = re.search(pattern, remote)
        if match:
            return match.group("repo")
    return ""


def bounded_text(value: object, limit: int = MAX_DETAIL_CHARS) -> str:
    text = str(value).replace("\r", " ").replace("\n", " ").replace("\t", " ")
    text = re.sub(r"\s+", " ", text).strip()
    for pattern in SECRET_PATTERNS:
        text = pattern.sub(lambda m: m.group(1) + "<redacted>" if m.groups() else "<redacted>", text)
    if len(text) > limit:
        return text[: max(limit - 3, 0)] + "..."
    return text


def result(
    name: str,
    status: str,
    verified_by: str,
    requires: str,
    details: Iterable[str],
) -> CheckResult:
    bounded_details = tuple(
        bounded_text(detail) for detail in list(details)[:MAX_DETAILS_PER_CHECK]
    )
    return CheckResult(
        name=name,
        status=status,
        verified_by=bounded_text(verified_by, 80),
        requires=bounded_text(requires, 120),
        details=bounded_details,
    )


def detail_value(check: CheckResult, key: str) -> str:
    prefix = f"{key}="
    for detail in check.details:
        if detail.startswith(prefix):
            return detail[len(prefix) :]
    return ""


def readiness_exit_code(results: Sequence[CheckResult]) -> int:
    blocking = {"fail", "unverified", "manual"}
    return 1 if any(check.status in blocking for check in results) else 0


def format_report(
    context: Mapping[str, str], results: Sequence[CheckResult], exit_code: int
) -> str:
    lines = [
        "# Minerva Release Readiness Check",
        f"timestamp_utc={bounded_text(context.get('timestamp_utc', '<unknown>'))}",
        f"repository={bounded_text(context.get('repository', '<unknown>'))}",
        f"commit={bounded_text(context.get('commit', '<unknown>'))}",
        f"domain={bounded_text(context.get('domain', DEFAULT_DOMAIN))}",
        "",
        "Output is bounded for public issue comments and omits tokens, local full paths, response bodies, and environment dumps.",
    ]
    for check in results:
        lines.extend(
            [
                "",
                f"[{check.name}] {check.status}",
                f"verified_by={check.verified_by}",
                f"requires={check.requires}",
            ]
        )
        lines.extend(f"- {detail}" for detail in check.details)
    lines.extend(["", f"overall={'pass' if exit_code == 0 else 'not_ready'}"])
    return "\n".join(lines)


if __name__ == "__main__":
    sys.exit(main())
