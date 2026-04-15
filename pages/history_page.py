"""History page — show and manage transcription history files."""
from __future__ import annotations

import logging
from pathlib import Path

import customtkinter as ctk

from utils.config import ConfigManager

logger = logging.getLogger(__name__)


class HistoryPage(ctk.CTkFrame):
    """Lists saved transcription .txt files and allows preview / deletion."""

    def __init__(self, master: ctk.CTkWidget, config: ConfigManager) -> None:
        super().__init__(master, fg_color="transparent")
        self._config = config
        self._selected: Path | None = None
        self._file_btns: list[ctk.CTkButton] = []
        self._build_ui()
        self._refresh()

    # ── UI Construction ────────────────────────────────────────────────────
    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ── Toolbar ──
        toolbar = ctk.CTkFrame(self, height=40)
        toolbar.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 0))
        toolbar.grid_columnconfigure(3, weight=1)

        ctk.CTkButton(
            toolbar, text="🔄 重新整理", width=110,
            command=self._refresh,
        ).grid(row=0, column=0, padx=(10, 5), pady=6)

        ctk.CTkButton(
            toolbar, text="🗑️ 刪除", width=80,
            fg_color="#c62828", hover_color="#b71c1c",
            command=self._delete_selected,
        ).grid(row=0, column=1, padx=5, pady=6)

        self._lbl_status = ctk.CTkLabel(toolbar, text="", anchor="w")
        self._lbl_status.grid(row=0, column=3, padx=10, pady=6, sticky="ew")

        # ── Body: list (left) + preview (right) ──
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        body.grid_columnconfigure(0, weight=0)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        # File list
        self._list_frame = ctk.CTkScrollableFrame(body, width=220, label_text="紀錄清單")
        self._list_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self._list_frame.grid_columnconfigure(0, weight=1)

        # Preview area
        preview_wrap = ctk.CTkFrame(body)
        preview_wrap.grid(row=0, column=1, sticky="nsew")
        preview_wrap.grid_columnconfigure(0, weight=1)
        preview_wrap.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(preview_wrap, text="預覽", anchor="w").grid(
            row=0, column=0, padx=10, pady=(6, 0), sticky="w",
        )

        self._preview = ctk.CTkTextbox(preview_wrap, wrap="word", state="disabled")
        self._preview.grid(row=1, column=0, sticky="nsew", padx=8, pady=8)

    # ── Public ────────────────────────────────────────────────────────────
    def _get_history_dir(self) -> Path:
        return Path(self._config.get("history_dir", "history"))

    def _refresh(self) -> None:
        """Reload file list from the history directory."""
        # Clear existing buttons
        for btn in self._file_btns:
            btn.destroy()
        self._file_btns.clear()
        self._selected = None

        hdir = self._get_history_dir()
        if not hdir.exists():
            self._lbl_status.configure(text="目錄不存在")
            return

        files = sorted(hdir.glob("*.txt"), reverse=True)
        if not files:
            self._lbl_status.configure(text="無紀錄")
            return

        for i, fp in enumerate(files):
            btn = ctk.CTkButton(
                self._list_frame,
                text=fp.name,
                anchor="w",
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray85", "gray25"),
                command=lambda p=fp: self._show_entry(p),
            )
            btn.grid(row=i, column=0, sticky="ew", padx=4, pady=2)
            self._file_btns.append(btn)

        self._lbl_status.configure(text=f"{len(files)} 筆紀錄")

    def _show_entry(self, fpath: Path) -> None:
        self._selected = fpath
        try:
            text = fpath.read_text(encoding="utf-8")
        except Exception as exc:
            text = f"[讀取失敗: {exc}]"
        self._preview.configure(state="normal")
        self._preview.delete("1.0", "end")
        self._preview.insert("1.0", text)
        self._preview.configure(state="disabled")

    def _delete_selected(self) -> None:
        if self._selected is None:
            self._lbl_status.configure(text="請先選擇紀錄")
            return
        try:
            self._selected.unlink()
            self._lbl_status.configure(text=f"✅ 已刪除 {self._selected.name}")
        except Exception as exc:
            self._lbl_status.configure(text=f"❌ 刪除失敗: {exc}")
        self._selected = None
        self._preview.configure(state="normal")
        self._preview.delete("1.0", "end")
        self._preview.configure(state="disabled")
        self._refresh()
