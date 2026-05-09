from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MIN_SETUPTOOLS_VERSION = (77,)


class InstallEntrypointSmokeTests(unittest.TestCase):
    def test_python_module_cli_doctor(self) -> None:
        result = self._run(
            [sys.executable, "-m", "minerva_kernel.cli", "doctor"],
            cwd=ROOT,
        )

        self.assertIn("Minerva doctor: repository skeleton is ready.", result.stdout)
        self.assertEqual(result.stderr, "")

    def test_local_editable_install_exposes_minerva_console_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            venv_path = tmp_path / "venv"

            venv_result = self._run(
                [sys.executable, "-m", "venv", str(venv_path)],
                timeout=120,
                fail_on_error=False,
            )
            if venv_result.returncode != 0 and _looks_like_missing_ensurepip(
                venv_result
            ):
                self.skipTest("python venv/ensurepip is unavailable in this environment")
            if venv_result.returncode != 0:
                self.fail(_format_command_failure(venv_result))

            venv_python = _venv_executable(venv_path, "python")
            _ensure_offline_setuptools(venv_python)

            self._run(
                [
                    str(venv_python),
                    "-m",
                    "pip",
                    "install",
                    "--no-index",
                    "--no-deps",
                    "--no-build-isolation",
                    "-e",
                    str(ROOT),
                ],
                cwd=tmp_path,
                timeout=180,
            )

            top_level = self._run(
                [
                    str(venv_python),
                    "-c",
                    (
                        "from importlib.metadata import distribution; "
                        "print(distribution('minerva-ai-kernel').read_text('top_level.txt') or '')"
                    ),
                ],
                cwd=tmp_path,
            )
            top_level_names = [
                line.strip() for line in top_level.stdout.splitlines() if line.strip()
            ]
            self.assertEqual(["minerva_kernel"], top_level_names)

            minerva = _venv_executable(venv_path, "minerva")
            result = self._run([str(minerva), "doctor"], cwd=tmp_path)

        self.assertIn("Minerva doctor: repository skeleton is ready.", result.stdout)
        self.assertEqual(result.stderr, "")

    def _run(
        self,
        args: list[str],
        *,
        cwd: str | Path | None = None,
        timeout: int = 60,
        fail_on_error: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            args,
            cwd=cwd,
            env=_base_env(),
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        if fail_on_error and result.returncode != 0:
            self.fail(_format_command_failure(result))
        return result


def _format_command_failure(result: subprocess.CompletedProcess[str]) -> str:
    return (
        f"command failed with exit code {result.returncode}: {result.args}\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )


def _looks_like_missing_ensurepip(result: subprocess.CompletedProcess[str]) -> bool:
    combined = f"{result.stdout}\n{result.stderr}".lower()
    return "ensurepip is not available" in combined or "python3-venv" in combined


def _ensure_offline_setuptools(venv_python: Path) -> None:
    version = _setuptools_version(venv_python)
    if version is not None and version >= MIN_SETUPTOOLS_VERSION:
        return

    source = _find_compatible_setuptools_source(venv_python)
    if source is None:
        raise AssertionError(
            "editable install smoke test needs setuptools>=77 available from "
            "the fresh venv or an existing local site-packages directory"
        )

    target = _venv_site_packages(venv_python)
    for existing in _setuptools_install_paths(target):
        _remove_path(existing)
    for path in _setuptools_install_paths(source):
        destination = target / path.name
        if path.is_dir():
            shutil.copytree(path, destination, dirs_exist_ok=True)
        else:
            shutil.copy2(path, destination)

    version = _setuptools_version(venv_python)
    if version is None or version < MIN_SETUPTOOLS_VERSION:
        raise AssertionError("failed to seed offline setuptools>=77 into test venv")


def _find_compatible_setuptools_source(venv_python: Path) -> Path | None:
    for candidate in _candidate_site_packages():
        version = _setuptools_version(venv_python, pythonpath=candidate)
        if version is not None and version >= MIN_SETUPTOOLS_VERSION:
            return candidate
    return None


def _candidate_site_packages() -> list[Path]:
    candidates: list[Path] = []
    for entry in sys.path:
        if not entry:
            continue
        path = Path(entry)
        if (path / "setuptools").is_dir():
            candidates.append(path)

    local_venv_lib = ROOT / ".venv" / "lib"
    if local_venv_lib.is_dir():
        candidates.extend(
            path
            for path in local_venv_lib.glob("python*/site-packages")
            if (path / "setuptools").is_dir()
        )

    deduped: list[Path] = []
    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved not in seen:
            deduped.append(candidate)
            seen.add(resolved)
    return deduped


def _setuptools_install_paths(site_packages: Path) -> list[Path]:
    names = ["setuptools", "_distutils_hack", "pkg_resources", "distutils-precedence.pth"]
    paths = [site_packages / name for name in names]
    paths.extend(site_packages.glob("setuptools-*.dist-info"))
    return [path for path in paths if path.exists()]


def _setuptools_version(
    python: Path,
    *,
    pythonpath: Path | None = None,
) -> tuple[int, ...] | None:
    env = _base_env()
    if pythonpath is not None:
        env["PYTHONPATH"] = str(pythonpath)
    result = subprocess.run(
        [str(python), "-c", "import setuptools; print(setuptools.__version__)"],
        env=env,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    if result.returncode != 0:
        return None
    return _version_tuple(result.stdout.strip())


def _version_tuple(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in re.findall(r"\d+", version)[:3])


def _venv_site_packages(venv_python: Path) -> Path:
    result = subprocess.run(
        [
            str(venv_python),
            "-c",
            "import sysconfig; print(sysconfig.get_paths()['purelib'])",
        ],
        env=_base_env(),
        text=True,
        capture_output=True,
        timeout=30,
        check=True,
    )
    return Path(result.stdout.strip())


def _remove_path(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()


def _base_env() -> dict[str, str]:
    env = os.environ.copy()
    env["PIP_CONFIG_FILE"] = os.devnull
    env["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
    env["PIP_NO_CACHE_DIR"] = "1"
    env["PIP_NO_INPUT"] = "1"
    return env


def _venv_executable(venv_path: Path, executable: str) -> Path:
    if os.name == "nt":
        suffix = ".exe" if executable != "python" else ".exe"
        return venv_path / "Scripts" / f"{executable}{suffix}"
    return venv_path / "bin" / executable


if __name__ == "__main__":
    unittest.main()
