"""Compatibility shim for Python 3.12+.

This project depends on `japanize_matplotlib`, which (as of 1.1.3) imports
`distutils.version.LooseVersion`. The standard-library `distutils` module was
removed in Python 3.12+, so we provide a tiny subset used by that dependency.
"""

from __future__ import annotations

__all__ = ["version"]

