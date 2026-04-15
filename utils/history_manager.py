"""History manager — saves transcribed audio WAV and text to ./history/.

Each entry is saved as a pair of files:
    history/YYYYMMDD_HHMMSS.wav   — raw audio (soundfile)
    history/YYYYMMDD_HHMMSS.txt   — transcription text (UTF-8)

All I/O runs in a daemon thread so the UI is never blocked.
"""

from __future__ import annotations

import logging
import threading
from datetime import datetime
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)


def save_entry(
    audio_np: np.ndarray,
    sample_rate: int,
    text: str,
    history_dir: str = "history",
) -> None:
    """Queue a non-blocking save of *audio_np* + *text* to *history_dir*.

    Returns immediately; the actual write happens in a daemon thread.
    """

    def _worker() -> None:
        try:
            dir_path = Path(history_dir)
            dir_path.mkdir(parents=True, exist_ok=True)

            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            wav_path = dir_path / f"{ts}.wav"
            txt_path = dir_path / f"{ts}.txt"

            import soundfile as sf  # soundfile is already a project dep

            sf.write(str(wav_path), audio_np, sample_rate)
            txt_path.write_text(text, encoding="utf-8")
            logger.debug("History saved: %s", wav_path)
        except Exception as exc:
            logger.warning("History save failed: %s", exc)

    threading.Thread(target=_worker, daemon=True).start()
