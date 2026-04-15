"""VoiceForge — Qwen3 本地語音轉錄與智慧潤稿工具.

Entry point: initialises the GUI and shared services.
"""

from __future__ import annotations

import logging
import sys
import threading

import customtkinter as ctk

from core.asr_engine import ASREngine
from pages.file_page import FilePage
from pages.polish_page import PolishPage
from pages.realtime_page import RealtimePage
from pages.settings_page import SettingsPage
from utils.config import ConfigManager
from utils.model_manager import ModelManager
from pages.history_page import HistoryPage
from utils.i18n import set_language
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("VoiceForge")


class App(ctk.CTk):
    """Main application window with four tabs."""

    WIDTH = 1000
    HEIGHT = 680

    def __init__(self) -> None:
        # ── Early config for theme/language (must be before super().__init__()) ──
        _cfg_early = ConfigManager()
        _theme = _cfg_early.get("ui_theme_color", "blue")
        _theme_path = Path(__file__).parent / "themes" / f"{_theme}.json"
        ctk.set_default_color_theme(str(_theme_path) if _theme_path.exists() else _theme)
        set_language(_cfg_early.get("ui_language", "zh"))

        super().__init__()

        # ── Window setup ──
        self.title("VoiceForge — Qwen3 語音轉錄")
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        self.minsize(800, 520)

        # ── Shared services ──
        self._config = ConfigManager()
        self._model_mgr = ModelManager(self._config.get("model_dir", "./models"))
        self._engine = ASREngine()

        ctk.set_appearance_mode(self._config.get("theme", "dark"))

        # ── Layout ──
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._tabs = ctk.CTkTabview(self, anchor="nw")
        self._tabs.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        tab_rt = self._tabs.add("🎙️ 即時轉錄")
        tab_file = self._tabs.add("📂 檔案轉錄")
        tab_polish = self._tabs.add("✨ 智慧潤稿")
        tab_history = self._tabs.add("📋 歷史紀錄")
        tab_settings = self._tabs.add("⚙️ 設定")

        for tab in (tab_rt, tab_file, tab_polish, tab_history, tab_settings):
            tab.grid_columnconfigure(0, weight=1)
            tab.grid_rowconfigure(0, weight=1)

        # Pages
        self._rt_page = RealtimePage(tab_rt, self._engine, self._config)
        self._rt_page.grid(row=0, column=0, sticky="nsew")

        self._file_page = FilePage(tab_file, self._engine, self._config)
        self._file_page.grid(row=0, column=0, sticky="nsew")

        self._polish_page = PolishPage(tab_polish, self._config)
        self._polish_page.grid(row=0, column=0, sticky="nsew")

        self._history_page = HistoryPage(tab_history, self._config)
        self._history_page.grid(row=0, column=0, sticky="nsew")

        self._settings_page = SettingsPage(
            tab_settings, self._config, self._engine, self._model_mgr,
            on_shortcut_changed=self._rt_page.refresh_ptt,
        )
        self._settings_page.grid(row=0, column=0, sticky="nsew")

        # ── Auto-load default model in background ──
        self._try_autoload()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self) -> None:
        """Unload model to free VRAM, then destroy window."""
        try:
            self._engine.unload()
        except Exception:
            pass
        self.destroy()

    def _try_autoload(self) -> None:
        """If the default model is already downloaded, load it on startup."""
        name = self._config.get("default_model", "Qwen3-ASR-0.6B")
        if not self._model_mgr.is_downloaded(name):
            logger.info("Default model %s not downloaded — skipping autoload", name)
            return

        local = self._model_mgr.local_path(name)
        device = self._config.get("device", "auto")
        tokens = self._config.get("max_new_tokens", 256)

        def _loader() -> None:
            logger.info("Auto-loading model %s (device=%s) …", name, device)
            try:
                self._engine.load(local, device=device, max_new_tokens=tokens)
                logger.info("Model ready on %s", self._engine._device)
                return
            except Exception as exc:
                logger.warning("Load on '%s' failed: %s", device, exc)

            if device != "cpu":
                logger.info("Falling back to CPU …")
                try:
                    self._engine.load(local, device="cpu", max_new_tokens=tokens)
                    logger.info("Model ready on cpu (fallback)")
                except Exception:
                    logger.exception("CPU fallback also failed for %s", name)

        threading.Thread(target=_loader, daemon=True).start()


def main() -> None:
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
