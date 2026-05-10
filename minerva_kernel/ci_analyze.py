from __future__ import annotations

import time
from pathlib import Path

from .observe import DEFAULT_TAIL_CHARS
from .types import Observation


def observation_from_ci_log(
    path: str | Path,
    *,
    job_name: str = "ci-log",
    tail_chars: int = DEFAULT_TAIL_CHARS,
) -> Observation:
    if tail_chars <= 0:
        raise ValueError("tail_chars must be greater than zero")

    log_path = Path(path)
    started = time.monotonic()
    stderr_tail, truncated = _read_text_tail(log_path, tail_chars)
    duration_ms = max(0, int(round((time.monotonic() - started) * 1000)))

    return Observation(
        command=f"ci-analyze {job_name} {log_path}",
        cwd=str(Path.cwd()),
        exit_code=1,
        stdout_tail="",
        stderr_tail=stderr_tail,
        duration_ms=duration_ms,
        source="ci_log",
        policy_summary=(
            "existing CI log analyzed locally; "
            f"log tail limited to {tail_chars} chars"
        ),
        runtime={
            "log_path": str(log_path),
            "job_name": job_name,
            "tail_chars": tail_chars,
            "stderr_truncated": truncated,
            "network_status": "unknown",
        },
    )


def _read_text_tail(path: Path, tail_chars: int) -> tuple[str, bool]:
    data = path.read_bytes()
    text = data.decode("utf-8", errors="replace")
    if len(text) <= tail_chars:
        return text, False
    return text[-tail_chars:], True
