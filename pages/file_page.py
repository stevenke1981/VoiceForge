"""File transcription page — select audio files and batch-transcribe."""

from __future__ import annotations

import logging
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from core.asr_engine import ASREngine
from utils.audio_utils import SUPPORTED_EXTENSIONS

logger = logging.getLogger(__name__)


class FilePage(ctk.CTkFrame):
    """Tab frame for file-based batch transcription."""

    def __init__(self, master: ctk.CTkBaseClass, engine: ASREngine, config: object) -> None:
        super().__init__(master, fg_color="transparent")
        self._engine = engine
        self._config = config
        self._files: list[Path] = []
        self._results: list[tuple[Path, object]] = []
        self._build_ui()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Top controls
        top = ctk.CTkFrame(self)
        top.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        top.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            top, text="📂 選擇檔案", width=120, command=self._select_files,
        ).grid(row=0, column=0, padx=5, pady=8)

        self._lbl_files = ctk.CTkLabel(top, text="尚未選擇檔案", anchor="w")
        self._lbl_files.grid(row=0, column=1, padx=10, pady=8, sticky="w")

        # Language + transcribe
        mid = ctk.CTkFrame(self)
        mid.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        mid.grid_columnconfigure(2, weight=1)

        ctk.CTkLabel(mid, text="語言:").grid(row=0, column=0, padx=(8, 4), pady=8)
        self._lang_var = ctk.StringVar(value="auto")
        ctk.CTkOptionMenu(
            mid, variable=self._lang_var, width=100,
            values=["auto", "zh", "en", "ja", "ko", "fr", "de", "es"],
        ).grid(row=0, column=1, padx=(0, 10), pady=8)

        self._ts_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(mid, text="時間戳記", variable=self._ts_var).grid(
            row=0, column=2, padx=5, pady=8, sticky="w",
        )

        self._btn_run = ctk.CTkButton(
            mid, text="▶️ 開始辨識", width=120, command=self._run_transcription,
            fg_color="#2e7d32", hover_color="#1b5e20",
        )
        self._btn_run.grid(row=0, column=3, padx=5, pady=8)

        self._progress = ctk.CTkProgressBar(mid, width=200)
        self._progress.grid(row=0, column=4, padx=10, pady=8)
        self._progress.set(0)

        # Result area
        self._txt = ctk.CTkTextbox(self, font=ctk.CTkFont(size=14))
        self._txt.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)

        # Bottom bar
        bottom = ctk.CTkFrame(self)
        bottom.grid(row=3, column=0, sticky="ew", padx=10, pady=(5, 10))
        bottom.grid_columnconfigure(0, weight=1)

        self._lbl_status = ctk.CTkLabel(bottom, text="就緒", anchor="w")
        self._lbl_status.grid(row=0, column=0, padx=10, pady=5, sticky="w")

        ctk.CTkButton(bottom, text="💾 匯出", width=80, command=self._export).grid(
            row=0, column=1, padx=5, pady=5,
        )
        ctk.CTkButton(bottom, text="📋 複製", width=80, command=self._copy).grid(
            row=0, column=2, padx=5, pady=5,
        )
        ctk.CTkButton(bottom, text="🎬 SRT", width=80, command=self._export_srt).grid(
            row=0, column=3, padx=5, pady=5,
        )

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _select_files(self) -> None:
        ext_list = " ".join(f"*{e}" for e in SUPPORTED_EXTENSIONS)
        paths = filedialog.askopenfilenames(
            title="選擇音訊檔案",
            filetypes=[("Audio files", ext_list), ("All files", "*.*")],
        )
        if paths:
            self._files = [Path(p) for p in paths]
            self._lbl_files.configure(text=f"已選擇 {len(self._files)} 個檔案")

    def _run_transcription(self) -> None:
        if not self._files:
            self._lbl_status.configure(text="⚠️ 請先選擇音訊檔案")
            return
        if not self._engine.is_loaded:
            self._lbl_status.configure(text="⚠️ 請先在設定頁面下載並載入模型")
            return

        self._btn_run.configure(state="disabled")
        self._lbl_status.configure(text="⏳ 辨識中...")
        self._progress.set(0)
        self._txt.delete("1.0", tk.END)
        self._results.clear()

        lang = self._lang_var.get()
        lang_arg = None if lang == "auto" else lang
        ts = self._ts_var.get()
        files = list(self._files)

        def _worker() -> None:
            total = len(files)
            for idx, fpath in enumerate(files, 1):
                try:
                    result = self._engine.transcribe(
                        str(fpath), language=lang_arg, return_timestamps=ts,
                    )
                    self.after(0, lambda r=result, f=fpath: self._append_result(f, r))
                except Exception as exc:
                    logger.exception("Failed: %s", fpath)
                    self.after(0, lambda f=fpath, e=str(exc): self._append_error(f, e))

                self.after(0, lambda v=idx / total: self._progress.set(v))

            self.after(0, self._on_done)

        threading.Thread(target=_worker, daemon=True).start()

    def _append_result(self, fpath: Path, result: object) -> None:
        header = f"── {fpath.name} ──"
        lang_tag = f" [{result.language}]" if result.language else ""
        self._txt.insert(tk.END, f"{header}{lang_tag}\n{result.text}\n\n")
        self._txt.see(tk.END)
        self._results.append((fpath, result))

    def _append_error(self, fpath: Path, error: str) -> None:
        self._txt.insert(tk.END, f"── {fpath.name} ── ❌ {error}\n\n")
        self._txt.see(tk.END)

    def _on_done(self) -> None:
        self._btn_run.configure(state="normal")
        self._lbl_status.configure(text=f"✅ 完成 — {len(self._files)} 個檔案")

    def _export(self) -> None:
        text = self._txt.get("1.0", tk.END).strip()
        if not text:
            return
        path = filedialog.asksaveasfilename(
            title="匯出辨識結果",
            defaultextension=".txt",
            filetypes=[("Text", "*.txt"), ("All", "*.*")],
        )
        if path:
            Path(path).write_text(text, encoding="utf-8")
            self._lbl_status.configure(text=f"已匯出: {path}")

    def _copy(self) -> None:
        text = self._txt.get("1.0", tk.END).strip()
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)
            self._lbl_status.configure(text="已複製到剪貼簿")

    @staticmethod
    def _secs_to_srt(s: float) -> str:
        ms = int(round(s * 1000))
        h, ms = divmod(ms, 3_600_000)
        m, ms = divmod(ms, 60_000)
        sec, ms = divmod(ms, 1000)
        return f"{h:02d}:{m:02d}:{sec:02d},{ms:03d}"

    def _export_srt(self) -> None:
        if not self._results:
            self._lbl_status.configure(text="⚠️ 尚無辨識結果可輸出")
            return
        exported = 0
        for fpath, result in self._results:
            stamps = getattr(result, "timestamps", None) or []
            if not stamps:
                continue
            lines: list[str] = []
            for i, seg in enumerate(stamps, 1):
                start = self._secs_to_srt(seg["start"])
                end   = self._secs_to_srt(seg["end"])
                text  = seg["text"].strip()
                lines.append(f"{i}\n{start} --> {end}\n{text}\n")
            srt_text = "\n".join(lines)
            out = fpath.with_suffix(".srt")
            out.write_text(srt_text, encoding="utf-8")
            exported += 1
        if exported:
            self._lbl_status.configure(text=f"✅ 已匯出 {exported} 個 SRT 檔案")
        else:
            self._lbl_status.configure(text="⚠️ 請先勾選時間戳記後再辨識")
