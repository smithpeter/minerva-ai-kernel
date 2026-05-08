from __future__ import annotations

import base64
import csv
import hashlib
import io
import os
import re
import subprocess
import sys
import tempfile
import tomllib
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class InstallEntrypointSmokeTests(unittest.TestCase):
    def test_python_module_cli_doctor(self) -> None:
        result = self._run(
            [sys.executable, "-m", "minerva_kernel.cli", "doctor"],
            cwd=ROOT,
        )

        self.assertIn("Minerva doctor: repository skeleton is ready.", result.stdout)
        self.assertEqual(result.stderr, "")

    def test_local_install_exposes_minerva_console_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            wheel_path = _build_test_wheel(ROOT, tmp_path)
            venv_path = tmp_path / "venv"

            self._run([sys.executable, "-m", "venv", str(venv_path)], timeout=120)
            venv_python = _venv_executable(venv_path, "python")
            minerva = _venv_executable(venv_path, "minerva")

            self._run(
                [
                    str(venv_python),
                    "-m",
                    "pip",
                    "install",
                    "--no-index",
                    "--no-deps",
                    str(wheel_path),
                ],
                timeout=120,
            )
            result = self._run([str(minerva), "doctor"], cwd=tmp_path)

        self.assertIn("Minerva doctor: repository skeleton is ready.", result.stdout)
        self.assertEqual(result.stderr, "")

    def _run(
        self,
        args: list[str],
        *,
        cwd: str | Path | None = None,
        timeout: int = 60,
    ) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
        env["PIP_NO_CACHE_DIR"] = "1"
        result = subprocess.run(
            args,
            cwd=cwd,
            env=env,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        if result.returncode != 0:
            self.fail(
                f"command failed with exit code {result.returncode}: {args}\n"
                f"stdout:\n{result.stdout}\n"
                f"stderr:\n{result.stderr}"
            )
        return result


def _build_test_wheel(root: Path, destination: Path) -> Path:
    pyproject = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    project = pyproject["project"]
    name = str(project["name"])
    version = str(project["version"])
    distribution = _wheel_safe(name)
    dist_info = f"{distribution}-{version}.dist-info"
    wheel_path = destination / f"{distribution}-{version}-py3-none-any.whl"
    records: list[tuple[str, str, str]] = []

    with zipfile.ZipFile(wheel_path, "w", zipfile.ZIP_DEFLATED) as wheel:
        for path in sorted((root / "minerva_kernel").glob("*.py")):
            _write_wheel_file(wheel, records, path.relative_to(root).as_posix(), path)

        _write_wheel_bytes(
            wheel,
            records,
            f"{dist_info}/METADATA",
            _metadata(project).encode("utf-8"),
        )
        _write_wheel_bytes(
            wheel,
            records,
            f"{dist_info}/WHEEL",
            (
                "Wheel-Version: 1.0\n"
                "Generator: minerva-install-entrypoint-smoke\n"
                "Root-Is-Purelib: true\n"
                "Tag: py3-none-any\n"
            ).encode("utf-8"),
        )
        _write_wheel_bytes(
            wheel,
            records,
            f"{dist_info}/entry_points.txt",
            _entry_points(project).encode("utf-8"),
        )

        record_path = f"{dist_info}/RECORD"
        record_bytes = _record_bytes([*records, (record_path, "", "")])
        wheel.writestr(record_path, record_bytes)

    return wheel_path


def _metadata(project: dict[str, object]) -> str:
    authors = project.get("authors", [])
    author = ""
    if isinstance(authors, list) and authors:
        first_author = authors[0]
        if isinstance(first_author, dict):
            author = str(first_author.get("name", ""))

    lines = [
        "Metadata-Version: 2.1",
        f"Name: {project['name']}",
        f"Version: {project['version']}",
        f"Summary: {project.get('description', '')}",
        f"Requires-Python: {project.get('requires-python', '')}",
    ]
    if author:
        lines.append(f"Author: {author}")
    return "\n".join(lines) + "\n"


def _entry_points(project: dict[str, object]) -> str:
    scripts = project.get("scripts")
    if not isinstance(scripts, dict) or "minerva" not in scripts:
        raise AssertionError("pyproject.toml must define the minerva console script")

    lines = ["[console_scripts]"]
    for name, target in sorted(scripts.items()):
        lines.append(f"{name} = {target}")
    return "\n".join(lines) + "\n"


def _write_wheel_file(
    wheel: zipfile.ZipFile,
    records: list[tuple[str, str, str]],
    arcname: str,
    path: Path,
) -> None:
    _write_wheel_bytes(wheel, records, arcname, path.read_bytes())


def _write_wheel_bytes(
    wheel: zipfile.ZipFile,
    records: list[tuple[str, str, str]],
    arcname: str,
    data: bytes,
) -> None:
    wheel.writestr(arcname, data)
    digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=")
    records.append((arcname, f"sha256={digest.decode('ascii')}", str(len(data))))


def _record_bytes(rows: list[tuple[str, str, str]]) -> bytes:
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerows(rows)
    return output.getvalue().encode("utf-8")


def _wheel_safe(value: str) -> str:
    return re.sub(r"[^\w\d.]+", "_", value, flags=re.ASCII)


def _venv_executable(venv_path: Path, executable: str) -> Path:
    if os.name == "nt":
        suffix = ".exe" if executable != "python" else ".exe"
        return venv_path / "Scripts" / f"{executable}{suffix}"
    return venv_path / "bin" / executable


if __name__ == "__main__":
    unittest.main()
