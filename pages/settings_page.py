"""Settings page — model management, API keys, audio device, and appearance."""

from __future__ import annotations

import logging
import threading
import tkinter as tk

import customtkinter as ctk

from core.asr_engine import ASREngine
from core.audio_recorder import AudioRecorder
from utils.config import ConfigManager
from utils.model_manager import ModelManager

logger = logging.getLogger(__name__)


class SettingsPage(ctk.CTkFrame):
    """Tab frame for application settings."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        config: ConfigManager,
        engine: ASREngine,
        model_mgr: ModelManager,
        on_shortcut_changed: object = None,
    ) -> None:
        super().__init__(master, fg_color="transparent")
        self._config = config
        self._engine = engine
        self._model_mgr = model_mgr
        self._on_shortcut_changed = on_shortcut_changed
        self._build_ui()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(self)
        scroll.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        scroll.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        row = 0

        # ── Model Section ──
        row = self._section(scroll, "🤖 模型管理", row)

        ctk.CTkLabel(scroll, text="選擇模型:").grid(row=row, column=0, sticky="w", padx=10, pady=5)
        self._model_var = ctk.StringVar(value=self._config.get("default_model", "Qwen3-ASR-0.6B"))
        models = self._model_mgr.list_available()
        self._model_menu = ctk.CTkOptionMenu(scroll, variable=self._model_var, values=models, width=220)
        self._model_menu.grid(row=row, column=1, sticky="w", padx=10, pady=5)
        row += 1

        btn_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_frame.grid(row=row, column=0, columnspan=2, sticky="w", padx=10, pady=5)

        self._btn_download = ctk.CTkButton(
            btn_frame, text="⬇️ 下載模型", width=110, command=self._download_model,
        )
        self._btn_download.grid(row=0, column=0, padx=5)

        self._btn_load = ctk.CTkButton(
            btn_frame, text="📦 載入模型", width=110, command=self._load_model,
            fg_color="#2e7d32", hover_color="#1b5e20",
        )
        self._btn_load.grid(row=0, column=1, padx=5)

        self._btn_unload = ctk.CTkButton(
            btn_frame, text="🗑️ 卸載模型", width=110, command=self._unload_model,
            fg_color="#757575", hover_color="#616161",
        )
        self._btn_unload.grid(row=0, column=2, padx=5)
        row += 1

        self._lbl_model_status = ctk.CTkLabel(scroll, text="", anchor="w")
        self._lbl_model_status.grid(row=row, column=0, columnspan=2, sticky="w", padx=10, pady=2)
        row += 1

        self._download_progress = ctk.CTkProgressBar(scroll, width=400)
        self._download_progress.grid(row=row, column=0, columnspan=2, sticky="w", padx=10, pady=5)
        self._download_progress.set(0)
        row += 1

        # ── Device Section ──
        row = self._section(scroll, "🖥️ 推論裝置", row)

        ctk.CTkLabel(scroll, text="裝置:").grid(row=row, column=0, sticky="w", padx=10, pady=5)
        self._device_var = ctk.StringVar(value=self._config.get("device", "auto"))
        ctk.CTkOptionMenu(
            scroll, variable=self._device_var, width=160,
            values=["auto", "cpu", "cuda:0", "cuda:1"],
        ).grid(row=row, column=1, sticky="w", padx=10, pady=5)
        row += 1

        ctk.CTkLabel(scroll, text="最大生成 tokens:").grid(row=row, column=0, sticky="w", padx=10, pady=5)
        self._tokens_var = ctk.StringVar(value=str(self._config.get("max_new_tokens", 256)))
        ctk.CTkEntry(scroll, textvariable=self._tokens_var, width=100).grid(
            row=row, column=1, sticky="w", padx=10, pady=5,
        )
        row += 1

        # ── LLM API Keys ──
        row = self._section(scroll, "🔑 LLM API 金鑰", row)

        self._key_entries: dict[str, ctk.CTkEntry] = {}
        for label, key in [
            ("Anthropic API Key:", "anthropic_api_key"),
            ("OpenAI API Key:", "openai_api_key"),
            ("Google API Key:", "google_api_key"),
        ]:
            ctk.CTkLabel(scroll, text=label).grid(row=row, column=0, sticky="w", padx=10, pady=5)
            entry = ctk.CTkEntry(scroll, show="•", width=320)
            entry.insert(0, self._config.get(key, ""))
            entry.grid(row=row, column=1, sticky="w", padx=10, pady=5)
            self._key_entries[key] = entry
            row += 1

        ctk.CTkLabel(scroll, text="LLM 模型:").grid(row=row, column=0, sticky="w", padx=10, pady=5)
        self._llm_model_var = ctk.StringVar(value=self._config.get("llm_model", "claude-sonnet-4-20250514"))
        ctk.CTkEntry(scroll, textvariable=self._llm_model_var, width=320).grid(
            row=row, column=1, sticky="w", padx=10, pady=5,
        )
        row += 1

        # ── Audio Section ──
        row = self._section(scroll, "🎤 音訊裝置", row)

        devices = AudioRecorder.list_devices()
        dev_names = ["(預設)"] + [f"{d['index']}: {d['name']}" for d in devices]
        self._audio_dev_var = ctk.StringVar(value="(預設)")
        ctk.CTkOptionMenu(
            scroll, variable=self._audio_dev_var, width=320, values=dev_names,
        ).grid(row=row, column=0, columnspan=2, sticky="w", padx=10, pady=5)
        row += 1

        # ── Appearance ──
        row = self._section(scroll, "🎨 外觀", row)

        ctk.CTkLabel(scroll, text="主題:").grid(row=row, column=0, sticky="w", padx=10, pady=5)
        self._theme_var = ctk.StringVar(value=self._config.get("theme", "dark"))
        ctk.CTkOptionMenu(
            scroll, variable=self._theme_var, width=120,
            values=["dark", "light", "system"],
            command=self._change_theme,
        ).grid(row=row, column=1, sticky="w", padx=10, pady=5)
        row += 1

        # ── 顏色主題 ──
        ctk.CTkLabel(scroll, text="顏色主題:").grid(row=row, column=0, sticky="w", padx=10, pady=5)
        self._color_theme_var = ctk.StringVar(value=self._config.get("ui_theme_color", "blue"))
        ctk.CTkOptionMenu(
            scroll, variable=self._color_theme_var, width=120,
            values=["blue", "green", "dark-blue", "ocean", "warm"],
        ).grid(row=row, column=1, sticky="w", padx=10, pady=5)
        row += 1

        # ── 介面語言 ──
        ctk.CTkLabel(scroll, text="介面語言:").grid(row=row, column=0, sticky="w", padx=10, pady=5)
        self._ui_lang_var = ctk.StringVar(value=self._config.get("ui_language", "zh"))
        ctk.CTkOptionMenu(
            scroll, variable=self._ui_lang_var, width=120,
            values=["zh", "en", "ja"],
        ).grid(row=row, column=1, sticky="w", padx=10, pady=5)
        row += 1

        # ── 快捷功能 — v0.3 ──
        row = self._section(scroll, "⌨️ 快捷功能", row)

        ctk.CTkLabel(scroll, text="Push to Talk:").grid(row=row, column=0, sticky="w", padx=10, pady=5)
        self._ptt_enabled_var = ctk.BooleanVar(value=self._config.get("push_to_talk_enabled", False))
        ctk.CTkSwitch(scroll, text="", variable=self._ptt_enabled_var, onvalue=True, offvalue=False).grid(
            row=row, column=1, sticky="w", padx=10, pady=5,
        )
        row += 1

        ctk.CTkLabel(scroll, text="PTT 快捷鍵:").grid(row=row, column=0, sticky="w", padx=10, pady=5)
        self._ptt_key_var = ctk.StringVar(value=self._config.get("push_to_talk_key", "ctrl+shift+space"))
        ctk.CTkEntry(scroll, textvariable=self._ptt_key_var, width=200, placeholder_text="例: ctrl+shift+space").grid(
            row=row, column=1, sticky="w", padx=10, pady=5,
        )
        row += 1

        ctk.CTkLabel(scroll, text="PTT 模式:").grid(row=row, column=0, sticky="w", padx=10, pady=5)
        self._ptt_mode_var = ctk.StringVar(value=self._config.get("push_to_talk_mode", "toggle"))
        ctk.CTkOptionMenu(
            scroll, variable=self._ptt_mode_var, width=160, values=["toggle", "hold"],
        ).grid(row=row, column=1, sticky="w", padx=10, pady=5)
        row += 1

        ctk.CTkLabel(scroll, text="轉錄後自動發送\n到焦點視窗:", justify="left").grid(row=row, column=0, sticky="w", padx=10, pady=5)
        self._auto_send_var = ctk.BooleanVar(value=self._config.get("auto_send_to_window", False))
        ctk.CTkSwitch(scroll, text="", variable=self._auto_send_var, onvalue=True, offvalue=False).grid(
            row=row, column=1, sticky="w", padx=10, pady=5,
        )
        row += 1

        # ── 文字轉換 — v0.4 ──
        row = self._section(scroll, "🔤 文字轉換 (OpenCC)", row)

        ctk.CTkLabel(scroll, text="啟用繁簡轉換:").grid(row=row, column=0, sticky="w", padx=10, pady=5)
        self._opencc_enabled_var = ctk.BooleanVar(value=self._config.get("opencc_enabled", False))
        ctk.CTkSwitch(scroll, text="", variable=self._opencc_enabled_var, onvalue=True, offvalue=False).grid(
            row=row, column=1, sticky="w", padx=10, pady=5,
        )
        row += 1

        ctk.CTkLabel(scroll, text="轉換模式:").grid(row=row, column=0, sticky="w", padx=10, pady=5)
        self._opencc_mode_var = ctk.StringVar(value=self._config.get("opencc_mode", "t2s"))
        ctk.CTkOptionMenu(
            scroll, variable=self._opencc_mode_var, width=160,
            values=["t2s", "s2t", "t2tw", "tw2s", "s2tw"],
        ).grid(row=row, column=1, sticky="w", padx=10, pady=5)
        row += 1
        ctk.CTkLabel(
            scroll, text="t2s=繁→簡  s2t=簡→繁  t2tw=繁→台灣繁體  tw2s=台灣繁→簡  s2tw=簡→台灣繁",
            font=ctk.CTkFont(size=11), text_color="gray",
        ).grid(row=row, column=0, columnspan=2, sticky="w", padx=10, pady=(0, 5))
        row += 1

        # ── 歷史記錄 — v0.4 ──
        row = self._section(scroll, "📁 歷史記錄", row)

        ctk.CTkLabel(scroll, text="儲存錄音和轉錄:").grid(row=row, column=0, sticky="w", padx=10, pady=5)
        self._save_history_var = ctk.BooleanVar(value=self._config.get("save_history", False))
        ctk.CTkSwitch(scroll, text="", variable=self._save_history_var, onvalue=True, offvalue=False).grid(
            row=row, column=1, sticky="w", padx=10, pady=5,
        )
        row += 1

        ctk.CTkLabel(scroll, text="存檔目錄:").grid(row=row, column=0, sticky="w", padx=10, pady=5)
        self._history_dir_var = ctk.StringVar(value=self._config.get("history_dir", "history"))
        ctk.CTkEntry(scroll, textvariable=self._history_dir_var, width=220, placeholder_text="history").grid(
            row=row, column=1, sticky="w", padx=10, pady=5,
        )
        row += 1

        # ── ForcedAligner — v0.5 ──
        row = self._section(scroll, "🔊 ForcedAligner", row)

        ctk.CTkLabel(scroll, text="ForcedAligner GPU:").grid(row=row, column=0, sticky="w", padx=10, pady=5)
        self._fa_gpu_var = ctk.BooleanVar(value=self._config.get("fa_use_gpu", False))
        ctk.CTkSwitch(scroll, text="使用 GPU", variable=self._fa_gpu_var).grid(
            row=row, column=1, sticky="w", padx=10, pady=5,
        )
        row += 1
        self._fa_dl_btn = ctk.CTkButton(
            scroll, text="📥 下載 FA 模型", width=160,
            command=self._download_fa,
        )
        self._fa_dl_btn.grid(row=row, column=0, columnspan=2, pady=5)
        row += 1

        # ── Save ──
        ctk.CTkButton(
            scroll, text="💾 儲存設定", width=160, command=self._save_settings,
            fg_color="#1565c0", hover_color="#0d47a1",
        ).grid(row=row, column=0, columnspan=2, pady=20)

        self._refresh_model_status()

    @staticmethod
    def _section(parent: ctk.CTkBaseClass, title: str, row: int) -> int:
        ctk.CTkLabel(
            parent, text=title, font=ctk.CTkFont(size=15, weight="bold"),
        ).grid(row=row, column=0, columnspan=2, sticky="w", padx=10, pady=(15, 5))
        return row + 1

    # ------------------------------------------------------------------
    # Model actions
    # ------------------------------------------------------------------

    def _download_model(self) -> None:
        name = self._model_var.get()
        if self._model_mgr.is_downloaded(name):
            self._lbl_model_status.configure(text=f"✅ {name} 已存在")
            return

        self._btn_download.configure(state="disabled")
        self._lbl_model_status.configure(text=f"⬇️ 下載 {name}...")
        self._download_progress.set(0)

        def _on_progress(status: str, pct: float) -> None:
            self.after(0, lambda: self._download_progress.set(pct))
            self.after(0, lambda: self._lbl_model_status.configure(text=f"⬇️ {status}"))

        def _worker() -> None:
            try:
                self._model_mgr.download(name, progress_cb=_on_progress)
                self.after(0, lambda: self._lbl_model_status.configure(text=f"✅ {name} 下載完成"))
                self.after(0, lambda: self._download_progress.set(1.0))
            except Exception as exc:
                logger.exception("Download failed")
                msg = f"❌ {exc}"
                self.after(0, lambda: self._lbl_model_status.configure(text=msg))
            finally:
                self.after(0, lambda: self._btn_download.configure(state="normal"))
                self.after(0, self._refresh_model_status)

        threading.Thread(target=_worker, daemon=True).start()

    def _load_model(self) -> None:
        name = self._model_var.get()
        local = self._model_mgr.local_path(name)

        if not self._model_mgr.is_downloaded(name):
            self._lbl_model_status.configure(text=f"⚠️ 請先下載 {name}")
            return

        if self._engine.is_loaded and self._engine.current_model == name:
            self._lbl_model_status.configure(text=f"✅ {name} 已載入 ({self._engine._device})")
            return

        self._btn_load.configure(state="disabled")
        self._lbl_model_status.configure(text=f"⏳ 載入 {name}...")

        device = self._device_var.get()
        tokens = int(self._tokens_var.get() or 256)

        def _worker() -> None:
            try:
                self._engine.load(local, device=device, max_new_tokens=tokens)
                self.after(0, lambda: self._lbl_model_status.configure(
                    text=f"✅ {name} 已載入 ({self._engine._device})",
                ))
            except Exception as exc:
                logger.exception("Load failed")
                msg = f"❌ {exc}"
                self.after(0, lambda: self._lbl_model_status.configure(text=msg))
            finally:
                self.after(0, lambda: self._btn_load.configure(state="normal"))

        threading.Thread(target=_worker, daemon=True).start()

    def _unload_model(self) -> None:
        self._engine.unload()
        self._lbl_model_status.configure(text="模型已卸載")

    def _refresh_model_status(self) -> None:
        downloaded = self._model_mgr.list_downloaded()
        parts = [f"已下載: {', '.join(downloaded) or '(無)'}"]
        if self._engine.is_loaded:
            parts.append(f"  |  已載入: {self._engine.current_model}")
        self._lbl_model_status.configure(text="  ".join(parts))
    def _download_fa(self) -> None:
        self._fa_dl_btn.configure(text="⏳ 下載中...", state="disabled")

        def _dl() -> None:
            try:
                from huggingface_hub import snapshot_download
                snapshot_download(
                    "Systran/faster-whisper-large-v2",
                    local_dir="./models/faster-whisper-large-v2",
                )
                self.after(0, lambda: self._fa_dl_btn.configure(text="✅ 下載完成", state="normal"))
            except Exception as exc:
                err = str(exc)
                self.after(0, lambda: self._fa_dl_btn.configure(text=f"❌ 失敗: {err}", state="normal"))

        threading.Thread(target=_dl, daemon=True).start()
    # ------------------------------------------------------------------
    # Settings
    # ------------------------------------------------------------------

    def _save_settings(self) -> None:
        updates = {
            "default_model": self._model_var.get(),
            "device": self._device_var.get(),
            "max_new_tokens": int(self._tokens_var.get() or 256),
            "theme": self._theme_var.get(),
            "llm_model": self._llm_model_var.get(),
            # v0.3 新增: 快捷功能
            "push_to_talk_enabled": self._ptt_enabled_var.get(),
            "push_to_talk_key": self._ptt_key_var.get().strip() or "ctrl+shift+space",
            "push_to_talk_mode": self._ptt_mode_var.get(),
            "auto_send_to_window": self._auto_send_var.get(),
            # v0.4 新增: 文字轉換 / 歷史記錄
            "opencc_enabled": self._opencc_enabled_var.get(),
            "opencc_mode": self._opencc_mode_var.get(),
            "save_history": self._save_history_var.get(),
            "history_dir": self._history_dir_var.get().strip() or "history",
            # v0.5 新增
            "ui_theme_color": self._color_theme_var.get(),
            "ui_language": self._ui_lang_var.get(),
            "fa_use_gpu": self._fa_gpu_var.get(),
        }

        for key, entry in self._key_entries.items():
            updates[key] = entry.get()

        # Parse audio device
        dev_str = self._audio_dev_var.get()
        if dev_str == "(預設)":
            updates["audio_device_index"] = None
        else:
            try:
                updates["audio_device_index"] = int(dev_str.split(":")[0])
            except ValueError:
                updates["audio_device_index"] = None

        self._config.update(updates)
        self._lbl_model_status.configure(text="✅ 設定已儲存")
        if callable(self._on_shortcut_changed):
            self._on_shortcut_changed()

    @staticmethod
    def _change_theme(value: str) -> None:
        ctk.set_appearance_mode(value)
