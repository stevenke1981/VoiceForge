"""Internationalization (i18n) support for VoiceForge.

Supported languages: zh (Traditional Chinese), en (English), ja (Japanese).

Usage
-----
    from utils.i18n import t, set_language
    set_language("zh")
    label_text = t("tab_realtime")
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# ── State ────────────────────────────────────────────────────────────────────

_LANG: str = "zh"
_STRINGS: dict[str, str] = {}
_LOCALES_DIR = Path(__file__).parent.parent / "locales"

# ── Public API ────────────────────────────────────────────────────────────────

def set_language(lang: str) -> None:
    """Load the locale JSON for *lang* and cache it.  Falls back to 'zh'."""
    global _LANG, _STRINGS

    supported = {"zh", "en", "ja"}
    if lang not in supported:
        logger.warning("Language '%s' not supported; falling back to 'zh'.", lang)
        lang = "zh"

    _LANG = lang
    locale_file = _LOCALES_DIR / f"{lang}.json"

    if locale_file.exists():
        try:
            _STRINGS = json.loads(locale_file.read_text(encoding="utf-8"))
            logger.info("Loaded locale: %s (%d keys)", lang, len(_STRINGS))
        except Exception as exc:
            logger.warning("Failed to load locale %s: %s", lang, exc)
            _STRINGS = {}
    else:
        logger.warning("Locale file not found: %s", locale_file)
        _STRINGS = {}


def t(key: str, default: str = "") -> str:
    """Return the translated string for *key*.

    Falls back to *default* if set, otherwise returns *key* itself so the UI
    always shows *something* even when a translation is missing.
    """
    return _STRINGS.get(key, default or key)


def current_language() -> str:
    """Return the ISO code of the currently active language."""
    return _LANG
