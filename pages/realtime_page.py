"""Realtime transcription page — record from mic and transcribe live."""

from __future__ import annotations

import logging
import threading
import tkinter as tk

import customtkinter as ctk
import numpy as np

from core.asr_engine import ASREngine
from core.audio_recorder import AudioRecorder
from utils import history_manager, opencc_converter

try:
    import ctypes as _ctypes
    import keyboard as _kbd
    import pyperclip as _clip
    _SHORTCUTS_AVAILABLE = True
except ImportError:
    _SHORTCUTS_AVAILABLE = False

logger = logging.getLogger(__name__)


class RealtimePage(ctk.CTkFrame):
    """Tab frame for real-time microphone transcription."""

    def __init__(self, master: ctk.CTkBaseClass, engine: ASREngine, config: object) -> None:
        super().__init__(master, fg_color="transparent")
        self._engine = engine
        self._config = config
        self._recorder = AudioRecorder(
            sample_rate=config.get("sample_rate", 16000),
            device_index=config.get("audio_device_index"),
        )
        self._ptt_hooks: list = []
        self._ptt_holding = False
        self._ptt_triggered = False   # True when recording was started via PTT
        self._auto_send_hwnd: int = 0  # Foreground HWND captured at PTT press time
        self._total_chars: int = self._config.get("total_chars_transcribed", 0)
        self._last_audio_np: np.ndarray | None = None
        self._last_sample_rate: int = config.get("sample_rate", 16000)
        self._build_ui()
        self.refresh_ptt()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Control bar
        ctrl = ctk.CTkFrame(self)
        ctrl.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        ctrl.grid_columnconfigure(2, weight=1)

        self._btn_record = ctk.CTkButton(
            ctrl, text="🎙️ 開始錄音", width=140,
            command=self._toggle_recording,
            fg_color="#e53935", hover_color="#b71c1c",
        )
        self._btn_record.grid(row=0, column=0, padx=5, pady=8)

        self._lbl_status = ctk.CTkLabel(ctrl, text="就緒", anchor="w")
        self._lbl_status.grid(row=0, column=1, padx=10, pady=8)

        self._lbl_ptt = ctk.CTkLabel(ctrl, text="", anchor="e", font=ctk.CTkFont(size=11))
        self._lbl_ptt.grid(row=0, column=2, padx=5, pady=8, sticky="e")

        self._lbl_time = ctk.CTkLabel(ctrl, text="00:00", font=ctk.CTkFont(size=14, weight="bold"))
        self._lbl_time.grid(row=0, column=3, padx=10, pady=8)

        # Language selector
        lang_frame = ctk.CTkFrame(self)
        lang_frame.grid(row=0, column=0, sticky="e", padx=(0, 170), pady=(10, 5))

        ctk.CTkLabel(lang_frame, text="語言:").grid(row=0, column=0, padx=(8, 4), pady=8)
        self._lang_var = ctk.StringVar(value="auto")
        self._lang_menu = ctk.CTkOptionMenu(
            lang_frame, variable=self._lang_var, width=100,
            values=["auto", "zh", "en", "ja", "ko", "fr", "de", "es"],
        )
        self._lang_menu.grid(row=0, column=1, padx=(0, 8), pady=8)

        # Text area
        self._txt = ctk.CTkTextbox(self, font=ctk.CTkFont(size=14))
        self._txt.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)

        # Bottom bar
        bottom = ctk.CTkFrame(self)
        bottom.grid(row=2, column=0, sticky="ew", padx=10, pady=(5, 10))
        bottom.grid_columnconfigure(0, weight=1)

        self._lbl_charcount = ctk.CTkLabel(
            bottom, text=f"📊 累計轉錄：{self._total_chars:,} 字",
            anchor="w", font=ctk.CTkFont(size=12),
        )
        self._lbl_charcount.grid(row=0, column=0, padx=10, pady=5, sticky="w")

        ctk.CTkButton(bottom, text="📋 複製", width=80, command=self._copy_text).grid(
            row=0, column=1, padx=5, pady=5,
        )
        ctk.CTkButton(bottom, text="🗑️ 清除", width=80, command=self._clear_text).grid(
            row=0, column=2, padx=5, pady=5,
        )

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _toggle_recording(self) -> None:
        if self._recorder.is_recording:
            self._stop_and_transcribe()
        else:
            self._start_recording()

    def _start_recording(self) -> None:
        if not self._engine.is_loaded:
            self._lbl_status.configure(text="⚠️ 請先在設定頁面下載並載入模型")
            return

        # If started via button click (not PTT), clear the target HWND so auto-send
        # is skipped (VoiceForge is the focused window; nowhere useful to paste).
        if not self._ptt_triggered:
            self._auto_send_hwnd = 0
        self._ptt_triggered = False  # reset for next recording

        self._recorder.set_device(self._config.get("audio_device_index"))
        self._recorder.start()
        self._btn_record.configure(text="⏹️ 停止錄音", fg_color="#1565c0", hover_color="#0d47a1")
        self._lbl_status.configure(text="🔴 錄音中...")
        self._update_timer()

    def _stop_and_transcribe(self) -> None:
        audio = self._recorder.stop()
        self._btn_record.configure(text="🎙️ 開始錄音", fg_color="#e53935", hover_color="#b71c1c")
        self._lbl_time.configure(text="00:00")

        if len(audio) < self._recorder.sample_rate * 0.3:
            self._lbl_status.configure(text="錄音太短，請重試")
            return

        self._lbl_status.configure(text="⏳ 辨識中...")
        self._btn_record.configure(state="disabled")
        self._last_audio_np = audio
        self._last_sample_rate = self._recorder.sample_rate

        def _worker() -> None:
            try:
                audio_input = (audio, self._recorder.sample_rate)
                lang = self._lang_var.get()
                lang_arg = None if lang == "auto" else lang
                result = self._engine.transcribe(
                    audio_input,
                    language=lang_arg,
                    return_timestamps=self._config.get("return_timestamps", False),
                )
                self.after(0, lambda: self._on_result(result))
            except Exception as exc:
                logger.exception("Transcription failed")
                msg = str(exc)
                self.after(0, lambda: self._on_error(msg))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_result(self, result: object) -> None:
        self._btn_record.configure(state="normal")
        # Apply OpenCC conversion if enabled
        text = result.text
        if self._config.get("opencc_enabled", False):
            mode = self._config.get("opencc_mode", "t2s")
            text = opencc_converter.convert(text, mode)
        lang_tag = f" [{result.language}]" if result.language else ""
        self._txt.insert(tk.END, f"{text}{lang_tag}\n\n")
        self._txt.see(tk.END)
        self._lbl_status.configure(text="✅ 辨識完成")
        # Update cumulative character count
        char_count = len(text.replace(" ", "").replace("\n", ""))
        self._total_chars += char_count
        self._config.set("total_chars_transcribed", self._total_chars)
        self._lbl_charcount.configure(text=f"📊 累計轉錄：{self._total_chars:,} 字")
        # Save to history in a background thread
        if self._config.get("save_history", False) and self._last_audio_np is not None:
            history_manager.save_entry(
                self._last_audio_np,
                self._last_sample_rate,
                text,
                self._config.get("history_dir", "history"),
            )
        self._auto_send(text)

    def _on_error(self, msg: str) -> None:
        self._btn_record.configure(state="normal")
        self._lbl_status.configure(text=f"❌ 錯誤: {msg[:60]}")

    def _update_timer(self) -> None:
        if not self._recorder.is_recording:
            return
        secs = self._recorder.get_duration()
        mins, s = divmod(int(secs), 60)
        self._lbl_time.configure(text=f"{mins:02d}:{s:02d}")
        self.after(500, self._update_timer)

    def _copy_text(self) -> None:
        text = self._txt.get("1.0", tk.END).strip()
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)
            self._lbl_status.configure(text="已複製到剪貼簿")

    def _clear_text(self) -> None:
        self._txt.delete("1.0", tk.END)
        self._lbl_status.configure(text="已清除")

    # ------------------------------------------------------------------
    # Push to Talk — v0.3 新增
    # ------------------------------------------------------------------

    def refresh_ptt(self) -> None:
        """Re-read config and re-register PTT hotkeys (call after settings save)."""
        self._teardown_ptt()
        if not _SHORTCUTS_AVAILABLE:
            self._lbl_ptt.configure(text="⚠️ 需安裝 keyboard / pyperclip 套件")
            return
        if not self._config.get("push_to_talk_enabled", False):
            self._lbl_ptt.configure(text="")
            return
        key = self._config.get("push_to_talk_key", "ctrl+shift+space")
        mode = self._config.get("push_to_talk_mode", "toggle")
        ok = self._setup_ptt()
        if ok:
            mode_label = "按住" if mode == "hold" else "切換"
            self._lbl_ptt.configure(text=f"🎯 PTT ({mode_label}): {key}")
        else:
            self._lbl_ptt.configure(text="❌ PTT 設定失敗（試試以系統管理員身分執行）")

    def _setup_ptt(self) -> bool:
        """Register hotkey hooks. Returns True on success, False on failure."""
        key = self._config.get("push_to_talk_key", "ctrl+shift+space")
        mode = self._config.get("push_to_talk_mode", "toggle")
        try:
            if mode == "hold":
                # BUG FIX: do NOT call add_hotkey twice for the same key.
                # The keyboard library's state machine resets after the first match,
                # so the release variant (trigger_on_release=True) never fires.
                # Instead: add_hotkey handles the press; on_release_key handles release.
                last_key = key.split("+")[-1].strip()
                h_press = _kbd.add_hotkey(key, self._ptt_press, suppress=True)
                h_release = _kbd.on_release_key(last_key, lambda _e: self._ptt_release())
                self._ptt_hooks = [h_press, h_release]
            else:
                h = _kbd.add_hotkey(key, self._ptt_toggle, suppress=True)
                self._ptt_hooks = [h]
            return True
        except Exception as exc:
            logger.warning("PTT setup failed: %s", exc)
            self._ptt_hooks = []
            return False

    def _teardown_ptt(self) -> None:
        if not _SHORTCUTS_AVAILABLE:
            self._ptt_hooks = []
            return
        for h in self._ptt_hooks:
            try:
                _kbd.remove_hotkey(h)
            except Exception:
                pass
        self._ptt_hooks = []

    def _ptt_press(self) -> None:
        """PTT hold mode — key down → start recording."""
        if not self._ptt_holding and not self._recorder.is_recording:
            self._ptt_holding = True
            # Capture the foreground window NOW (before tkinter processes events)
            # so auto-send can target the correct external window later.
            try:
                self._auto_send_hwnd = _ctypes.windll.user32.GetForegroundWindow()
            except Exception:
                self._auto_send_hwnd = 0
            self._ptt_triggered = True
            self.after(0, self._start_recording)

    def _ptt_release(self) -> None:
        """PTT hold mode — all keys released → stop + transcribe."""
        if self._ptt_holding:
            self._ptt_holding = False
            if self._recorder.is_recording:
                self.after(0, self._stop_and_transcribe)

    def _ptt_toggle(self) -> None:
        """PTT toggle mode — each press toggles recording."""
        if self._recorder.is_recording:
            self.after(0, self._stop_and_transcribe)
        else:
            # Capture target window before VoiceForge processes any tkinter events
            try:
                self._auto_send_hwnd = _ctypes.windll.user32.GetForegroundWindow()
            except Exception:
                self._auto_send_hwnd = 0
            self._ptt_triggered = True
            self.after(0, self._start_recording)

    def destroy(self) -> None:
        """Clean up PTT hooks before destroying the widget."""
        self._teardown_ptt()
        super().destroy()

    # ------------------------------------------------------------------
    # Auto-send to window — v0.3 新增
    # ------------------------------------------------------------------

    def _auto_send(self, text: str) -> None:
        """Paste transcribed text to the target window captured at PTT press time."""
        if not _SHORTCUTS_AVAILABLE:
            return
        if not self._config.get("auto_send_to_window", False):
            return
        stripped = text.strip()
        if not stripped:
            return
        target_hwnd = self._auto_send_hwnd
        if not target_hwnd:
            # Recording was started via button (VoiceForge in focus) → skip auto-send
            self._lbl_status.configure(text="✅ 辨識完成　💡 PTT 模式才會自動發送")
            return

        def _do_send() -> None:
            import time
            time.sleep(0.15)  # Let tkinter finish rendering before injecting input
            try:
                _clip.copy(stripped)
                # Bring the target window to front then send Ctrl+V
                try:
                    _ctypes.windll.user32.SetForegroundWindow(target_hwnd)
                    time.sleep(0.05)
                except Exception:
                    pass  # SetForegroundWindow may fail; try keyboard.send anyway
                _kbd.send("ctrl+v")
                # Release all PTT modifier keys to prevent stuck keys in target window
                _ptt_key = self._config.get("push_to_talk_key", "ctrl+shift+space")
                for _part in _ptt_key.split("+"):
                    try:
                        _kbd.release(_part.strip())
                    except Exception:
                        pass
                self.after(0, lambda: self._lbl_status.configure(text="✅ 辨識完成　📤 已發送"))
            except Exception as exc:
                logger.warning("Auto-send failed: %s", exc)
                self.after(0, lambda: self._lbl_status.configure(text=f"✅ 辨識完成　❌ 發送失敗"))

        threading.Thread(target=_do_send, daemon=True).start()
