"""Test configuration for the new src-based implementation."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
LEGACY_SRC = ROOT / "legacy" / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(LEGACY_SRC) not in sys.path:
    sys.path.insert(1, str(LEGACY_SRC))
