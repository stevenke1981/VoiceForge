"""Audio utility helpers for VoiceForge.

Provides format conversion, resampling, and file info extraction.
"""

from __future__ import annotations

import io
import logging
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".wav", ".mp3", ".flac", ".ogg", ".m4a", ".wma", ".aac"}


def is_supported(path: str | Path) -> bool:
    return Path(path).suffix.lower() in SUPPORTED_EXTENSIONS


def load_audio(path: str | Path, target_sr: int = 16000) -> tuple[np.ndarray, int]:
    """Load an audio file and return (mono float32 ndarray, sample_rate).

    Uses soundfile for WAV/FLAC, falling back to pydub for other formats.
    """
    path = Path(path)
    suffix = path.suffix.lower()

    if suffix in {".wav", ".flac"}:
        return _load_soundfile(path, target_sr)
    return _load_pydub(path, target_sr)


def _load_soundfile(path: Path, target_sr: int) -> tuple[np.ndarray, int]:
    import soundfile as sf

    data, sr = sf.read(str(path), dtype="float32", always_2d=True)
    # Mix to mono
    if data.shape[1] > 1:
        data = data.mean(axis=1)
    else:
        data = data[:, 0]

    if sr != target_sr:
        data = _resample(data, sr, target_sr)
    return data, target_sr


def _load_pydub(path: Path, target_sr: int) -> tuple[np.ndarray, int]:
    from pydub import AudioSegment

    seg = AudioSegment.from_file(str(path))
    seg = seg.set_channels(1).set_frame_rate(target_sr).set_sample_width(2)

    samples = np.array(seg.get_array_of_samples(), dtype=np.float32)
    samples /= 32768.0
    return samples, target_sr


def _resample(data: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
    """Simple linear resampling. For production, consider librosa or scipy."""
    ratio = target_sr / orig_sr
    n_out = int(len(data) * ratio)
    indices = np.linspace(0, len(data) - 1, n_out)
    return np.interp(indices, np.arange(len(data)), data).astype(np.float32)


def ndarray_to_wav_bytes(data: np.ndarray, sr: int = 16000) -> bytes:
    """Convert float32 ndarray to WAV bytes in memory."""
    import soundfile as sf

    buf = io.BytesIO()
    sf.write(buf, data, sr, format="WAV", subtype="PCM_16")
    return buf.getvalue()


def get_duration(path: str | Path) -> float:
    """Return duration in seconds."""
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix in {".wav", ".flac"}:
        import soundfile as sf
        info = sf.info(str(path))
        return info.duration
    from pydub import AudioSegment
    seg = AudioSegment.from_file(str(path))
    return len(seg) / 1000.0
