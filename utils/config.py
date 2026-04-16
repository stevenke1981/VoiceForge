"""Configuration management for VoiceForge.

Loads and saves JSON config from ./config.json with sensible defaults.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Load .env on first import so all os.environ reads below see the values.
# dotenv never overwrites variables already set by the shell.
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env", override=False)
except ImportError:
    pass  # python-dotenv not installed; env vars must be set manually

# Mapping: config key → environment variable name
_ENV_KEY_MAP: dict[str, str] = {
    "google_api_key": "GOOGLE_API_KEY",
    "anthropic_api_key": "ANTHROPIC_API_KEY",
    "openai_api_key": "OPENAI_API_KEY",
}

_DEFAULTS: dict[str, Any] = {
    "model_dir": "./models",
    "default_model": "Qwen3-ASR-0.6B",
    "language": None,
    "device": "auto",
    "return_timestamps": False,
    "max_new_tokens": 256,
    "sample_rate": 16000,
    "llm_provider": "anthropic",
    "llm_model": "claude-sonnet-4-20250514",
    "anthropic_api_key": "",
    "openai_api_key": "",
    "google_api_key": "",
    "polish_prompt": "請潤飾以下語音辨識文字，修正錯字、加標點符號，保持原意：",
    "theme": "dark",
    "audio_device_index": None,
    # v0.3 新增: 快捷功能
    "push_to_talk_enabled": False,
    "push_to_talk_key": "ctrl+shift+space",
    "push_to_talk_mode": "toggle",
    "auto_send_to_window": False,
    # v0.4 新增: 文字轉換 / 歷史記錄 / 統計
    "opencc_enabled": False,
    "opencc_mode": "t2s",
    "save_history": False,
    "history_dir": "history",
    "total_chars_transcribed": 0,
    # v0.5 新增: UI 語言 / 顏色主題 / ForcedAligner GPU
    "ui_language": "zh",
    "ui_theme_color": "blue",
    "fa_use_gpu": False,
}

CONFIG_PATH = Path("config.json")


class ConfigManager:
    """Thread-safe JSON config backed by a local file."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or CONFIG_PATH
        self._data: dict[str, Any] = {}
        self._load()

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def get(self, key: str, default: Any = None) -> Any:
        # API keys: env var takes priority over config.json
        if key in _ENV_KEY_MAP:
            env_val = os.environ.get(_ENV_KEY_MAP[key], "")
            if env_val:
                return env_val
        return self._data.get(key, _DEFAULTS.get(key, default))

    def set(self, key: str, value: Any) -> None:
        self._data = {**self._data, key: value}
        self._save()

    def update(self, patch: dict[str, Any]) -> None:
        self._data = {**self._data, **patch}
        self._save()

    def all(self) -> dict[str, Any]:
        merged = {**_DEFAULTS, **self._data}
        return dict(merged)

    def reset(self) -> None:
        self._data = {}
        self._save()

    # ------------------------------------------------------------------
    # Internal I/O
    # ------------------------------------------------------------------

    def _load(self) -> None:
        if self._path.exists():
            try:
                raw = self._path.read_text(encoding="utf-8")
                self._data = json.loads(raw)
                logger.info("Config loaded from %s", self._path)
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning("Failed to load config, using defaults: %s", exc)
                self._data = {}
        else:
            logger.info("No config file found, creating defaults at %s", self._path)
            self._data = {}
            self._save()

    def _save(self) -> None:
        try:
            payload = json.dumps(self._data, ensure_ascii=False, indent=2)
            self._path.write_text(payload, encoding="utf-8")
        except OSError as exc:
            logger.error("Failed to save config: %s", exc)
