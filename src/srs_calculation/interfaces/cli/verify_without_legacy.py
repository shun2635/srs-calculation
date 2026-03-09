"""Verification command for running the root CLI without the legacy tree."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


REPO_ROOT = Path(__file__).resolve().parents[4]


def _resolve_poetry_bin() -> str:
    explicit = os.environ.get("POETRY_BIN")
    if explicit:
        return explicit

    discovered = shutil.which("poetry")
    if discovered:
        return discovered

    for candidate in (
        "/opt/homebrew/bin/poetry",
        "/usr/local/bin/poetry",
    ):
        if Path(candidate).exists():
            return candidate

    raise SystemExit(
        "poetry executable not found. Set POETRY_BIN or install poetry on PATH."
    )


def _run(command: list[str], *, cwd: Path) -> None:
    printable = " ".join(command)
    print(f"$ {printable}", flush=True)
    completed = subprocess.run(command, cwd=cwd, check=False)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


@contextmanager
def _temporarily_hide_legacy(repo_root: Path) -> Iterator[None]:
    legacy_dir = repo_root / "legacy"
    hidden_dir = repo_root / f".legacy.hidden.{os.getpid()}"

    if not legacy_dir.exists():
        yield
        return

    if hidden_dir.exists():
        raise SystemExit(f"temporary hidden legacy path already exists: {hidden_dir}")

    legacy_dir.rename(hidden_dir)
    try:
        yield
    finally:
        if hidden_dir.exists() and not legacy_dir.exists():
            hidden_dir.rename(legacy_dir)


def main() -> int:
    """Verify that the root CLI and tests still work without `legacy/`."""

    poetry_bin = _resolve_poetry_bin()
    commands = [
        [poetry_bin, "run", "srs-real-gen", "--help"],
        [poetry_bin, "run", "srs-game-gen", "--help"],
        [poetry_bin, "run", "srs-test"],
        [poetry_bin, "run", "srs-test", "tests/e2e", "-q"],
    ]

    with _temporarily_hide_legacy(REPO_ROOT):
        for command in commands:
            _run(command, cwd=REPO_ROOT)

    print("verification succeeded without legacy/", flush=True)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
