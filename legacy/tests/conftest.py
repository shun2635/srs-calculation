from __future__ import annotations

import sys
from pathlib import Path

# Ensure src-layout packages (and repo-local shims like distutils/) are importable in tests.
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(SRC))
