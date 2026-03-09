"""Poetry-friendly pytest entry point for the new implementation."""

from __future__ import annotations

import sys


def main() -> int:
    """Run pytest with repository defaults, forwarding any extra arguments."""

    try:
        import pytest
    except ModuleNotFoundError as exc:  # pragma: no cover
        raise SystemExit(
            "pytest is not installed in the active environment. "
            "Run 'poetry install' to install dev dependencies."
        ) from exc

    args = sys.argv[1:] or ["tests"]
    return int(pytest.main(args))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
