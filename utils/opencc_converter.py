"""OpenCC Traditional/Simplified Chinese converter wrapper.

Lazy-imports opencc so the app starts even when the package is absent.
Install: pip install opencc-python-reimplemented
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

_converter = None
_current_mode: str = ""


def is_available() -> bool:
    """Return True if the opencc package is importable."""
    try:
        import opencc  # noqa: F401
        return True
    except ImportError:
        return False


def _ensure(mode: str) -> object | None:
    """Return a cached OpenCC converter for *mode*, or None on failure."""
    global _converter, _current_mode
    if _converter is not None and _current_mode == mode:
        return _converter
    try:
        import opencc
        _converter = opencc.OpenCC(mode)
        _current_mode = mode
        return _converter
    except ImportError:
        logger.warning(
            "opencc-python-reimplemented not installed; "
            "run: pip install opencc-python-reimplemented"
        )
        return None
    except Exception as exc:
        logger.warning("OpenCC init failed (mode=%s): %s", mode, exc)
        return None


def convert(text: str, mode: str = "t2s") -> str:
    """Convert *text* using the given OpenCC *mode*.

    Returns the original text unchanged if opencc is unavailable or fails.

    Common modes:
        t2s  — Traditional → Simplified
        s2t  — Simplified → Traditional
        t2tw — Traditional (Mainland) → Traditional (Taiwan)
        tw2s — Traditional (Taiwan) → Simplified
        s2tw — Simplified → Traditional (Taiwan)
    """
    cc = _ensure(mode)
    if cc is None:
        return text
    try:
        return cc.convert(text)
    except Exception as exc:
        logger.warning("OpenCC conversion failed: %s", exc)
        return text
