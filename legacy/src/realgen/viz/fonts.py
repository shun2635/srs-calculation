"""Font helpers for Japanese labels in matplotlib."""

from __future__ import annotations

from typing import Iterable


def set_japanese_font_if_available(preferred: Iterable[str] | None = None) -> None:
    """Best-effort set a Japanese-capable font for matplotlib.

    Does nothing if matplotlib isn't available or no preferred font is found.
    """
    try:
        import matplotlib as mpl
        from matplotlib import font_manager
    except Exception:
        return

    preferred_list = list(preferred) if preferred is not None else [
        "IPAexGothic",
        "IPAGothic",
        "Noto Sans CJK JP",
        "Noto Sans JP",
        "Hiragino Sans",
        "Hiragino Kaku Gothic ProN",
        "Yu Gothic",
        "MS Gothic",
    ]

    available = {f.name for f in font_manager.fontManager.ttflist}
    for name in preferred_list:
        if name in available:
            mpl.rcParams["font.family"] = name
            return


__all__ = ["set_japanese_font_if_available"]

