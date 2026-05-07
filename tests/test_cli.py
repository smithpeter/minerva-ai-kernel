from __future__ import annotations

from minerva_kernel.cli import main


def test_cli_help(capsys) -> None:
    try:
        main()
    except SystemExit as exc:
        assert exc.code == 0
    out = capsys.readouterr().out
    assert "CPU-local failure interpreter" in out

