"""LLM polishing page — refine transcription text with an LLM."""

from __future__ import annotations

import logging
import threading
import tkinter as tk

import customtkinter as ctk

from core.llm_polish import LLMPolisher
from utils.polish_templates import POLISH_TEMPLATES, TRANSLATION_TEMPLATES

logger = logging.getLogger(__name__)

_PROVIDERS = ["anthropic", "openai", "google"]


class PolishPage(ctk.CTkFrame):
    """Tab frame for LLM text polishing."""

    def __init__(self, master: ctk.CTkBaseClass, config: object) -> None:
        super().__init__(master, fg_color="transparent")
        self._config = config
        self._polisher = LLMPolisher(config)
        self._build_ui()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Controls
        ctrl = ctk.CTkFrame(self)
        ctrl.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=(10, 5))
        ctrl.grid_columnconfigure(4, weight=1)

        ctk.CTkLabel(ctrl, text="LLM 提供者:").grid(row=0, column=0, padx=(8, 4), pady=8)
        self._provider_var = ctk.StringVar(value=self._config.get("llm_provider", "anthropic"))
        ctk.CTkOptionMenu(
            ctrl, variable=self._provider_var, width=120, values=_PROVIDERS,
        ).grid(row=0, column=1, padx=(0, 10), pady=8)

        # ── Template type (row=1) ──
        ctk.CTkLabel(ctrl, text="模板類型:").grid(row=1, column=0, padx=(8, 4), pady=5)
        self._tmpl_type_var = ctk.StringVar(value="潤稿模板")
        ctk.CTkOptionMenu(
            ctrl, variable=self._tmpl_type_var, width=120,
            values=["潤稿模板", "翻譯模板"],
            command=self._on_tmpl_type_changed,
        ).grid(row=1, column=1, padx=(0, 10), pady=5)

        # ── Template name (row=2) ──
        ctk.CTkLabel(ctrl, text="模板:").grid(row=2, column=0, padx=(8, 4), pady=5)
        self._tmpl_names = [t["name"] for t in POLISH_TEMPLATES]
        self._tmpl_var = ctk.StringVar(value=self._tmpl_names[0])
        self._tmpl_menu = ctk.CTkOptionMenu(
            ctrl, variable=self._tmpl_var, width=200,
            values=self._tmpl_names,
            command=self._on_tmpl_changed,
        )
        self._tmpl_menu.grid(row=2, column=1, padx=(0, 10), pady=5)
        self._current_system_prompt: str = POLISH_TEMPLATES[0]["prompt"]

        self._btn_polish = ctk.CTkButton(
            ctrl, text="✨ 潤稿", width=100, command=self._run_polish,
            fg_color="#6a1b9a", hover_color="#4a148c",
        )
        self._btn_polish.grid(row=0, column=2, padx=5, pady=8)

        self._lbl_status = ctk.CTkLabel(ctrl, text="就緒", anchor="w")
        self._lbl_status.grid(row=0, column=4, padx=10, pady=8, sticky="w")

        # Left — input
        lbl_in = ctk.CTkLabel(self, text="📝 原始文字", font=ctk.CTkFont(size=13, weight="bold"))
        lbl_in.grid(row=0, column=0, sticky="sw", padx=15, pady=(35, 0))

        self._txt_in = ctk.CTkTextbox(self, font=ctk.CTkFont(size=14))
        self._txt_in.grid(row=1, column=0, sticky="nsew", padx=(10, 5), pady=5)

        # Right — output
        lbl_out = ctk.CTkLabel(self, text="✨ 潤稿結果", font=ctk.CTkFont(size=13, weight="bold"))
        lbl_out.grid(row=0, column=1, sticky="sw", padx=15, pady=(35, 0))

        self._txt_out = ctk.CTkTextbox(self, font=ctk.CTkFont(size=14))
        self._txt_out.grid(row=1, column=1, sticky="nsew", padx=(5, 10), pady=5)

        # Bottom bar
        bottom = ctk.CTkFrame(self)
        bottom.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=(5, 10))
        bottom.grid_columnconfigure(0, weight=1)

        ctk.CTkButton(bottom, text="📋 複製結果", width=100, command=self._copy_output).grid(
            row=0, column=1, padx=5, pady=5,
        )
        ctk.CTkButton(bottom, text="⬅️ 用結果取代", width=110, command=self._replace_input).grid(
            row=0, column=2, padx=5, pady=5,
        )

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _run_polish(self) -> None:
        text = self._txt_in.get("1.0", tk.END).strip()
        if not text:
            self._lbl_status.configure(text="⚠️ 請輸入要潤稿的文字")
            return

        provider = self._provider_var.get()
        self._btn_polish.configure(state="disabled")
        self._lbl_status.configure(text="⏳ 潤稿中...")

        def _worker() -> None:
            try:
                result = self._polisher.polish(
                    text, provider=provider,
                    system_prompt=self._current_system_prompt or None,
                )
                self.after(0, lambda: self._on_result(result))
            except Exception as exc:
                logger.exception("Polish failed")
                msg = str(exc)
                self.after(0, lambda: self._on_error(msg))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_tmpl_type_changed(self, value: str) -> None:
        pool = POLISH_TEMPLATES if value == "潤稿模板" else TRANSLATION_TEMPLATES
        names = [t["name"] for t in pool]
        self._tmpl_menu.configure(values=names)
        self._tmpl_var.set(names[0])
        self._current_system_prompt = pool[0]["prompt"]

    def _on_tmpl_changed(self, value: str) -> None:
        pool = POLISH_TEMPLATES if self._tmpl_type_var.get() == "潤稿模板" else TRANSLATION_TEMPLATES
        for t in pool:
            if t["name"] == value:
                self._current_system_prompt = t["prompt"]
                break

    def _on_result(self, text: str) -> None:
        self._btn_polish.configure(state="normal")
        self._txt_out.delete("1.0", tk.END)
        self._txt_out.insert("1.0", text)
        self._lbl_status.configure(text="✅ 潤稿完成")

    def _on_error(self, msg: str) -> None:
        self._btn_polish.configure(state="normal")
        self._lbl_status.configure(text=f"❌ {msg[:80]}")

    def _copy_output(self) -> None:
        text = self._txt_out.get("1.0", tk.END).strip()
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)
            self._lbl_status.configure(text="已複製到剪貼簿")

    def _replace_input(self) -> None:
        text = self._txt_out.get("1.0", tk.END).strip()
        if text:
            self._txt_in.delete("1.0", tk.END)
            self._txt_in.insert("1.0", text)
            self._lbl_status.configure(text="已將結果放回輸入欄")

    def set_input(self, text: str) -> None:
        """Programmatically set input text (e.g. from other pages)."""
        self._txt_in.delete("1.0", tk.END)
        self._txt_in.insert("1.0", text)
