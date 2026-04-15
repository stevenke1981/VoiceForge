"""Microphone audio recorder using sounddevice.

Records 16 kHz mono float32 audio in a background thread,
exposing start / stop / get_audio controls for the GUI.
"""

from __future__ import annotations

import logging
import threading
from typing import Callable

import numpy as np
import sounddevice as sd

logger = logging.getLogger(__name__)

AudioChunkCallback = Callable[[np.ndarray], None]


class AudioRecorder:
    """Stream-based microphone recorder."""

    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        device_index: int | None = None,
        chunk_duration: float = 0.5,
    ) -> None:
        self._sr = sample_rate
        self._channels = channels
        self._device_index = device_index
        self._chunk_samples = int(sample_rate * chunk_duration)

        self._stream: sd.InputStream | None = None
        self._chunks: list[np.ndarray] = []
        self._lock = threading.Lock()
        self._recording = False
        self._on_chunk: AudioChunkCallback | None = None

    @property
    def is_recording(self) -> bool:
        return self._recording

    @property
    def sample_rate(self) -> int:
        return self._sr

    def set_device(self, device_index: int | None) -> None:
        self._device_index = device_index

    def set_on_chunk(self, callback: AudioChunkCallback | None) -> None:
        """Set a callback that fires for each audio chunk during recording."""
        self._on_chunk = callback

    def start(self) -> None:
        """Start recording from the microphone."""
        if self._recording:
            return

        with self._lock:
            self._chunks = []

        self._stream = sd.InputStream(
            samplerate=self._sr,
            channels=self._channels,
            dtype="float32",
            device=self._device_index,
            blocksize=self._chunk_samples,
            callback=self._audio_callback,
        )
        self._stream.start()
        self._recording = True
        logger.info("Recording started (sr=%d, device=%s)", self._sr, self._device_index)

    def stop(self) -> np.ndarray:
        """Stop recording and return the full audio as a float32 ndarray."""
        if not self._recording:
            return np.array([], dtype=np.float32)

        self._recording = False
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        with self._lock:
            if not self._chunks:
                return np.array([], dtype=np.float32)
            audio = np.concatenate(self._chunks, axis=0)
            self._chunks = []

        logger.info("Recording stopped — %.1f seconds captured", len(audio) / self._sr)
        return audio

    def get_current_audio(self) -> np.ndarray:
        """Return a copy of audio captured so far (non-destructive)."""
        with self._lock:
            if not self._chunks:
                return np.array([], dtype=np.float32)
            return np.concatenate(self._chunks, axis=0)

    def get_duration(self) -> float:
        """Return current recording duration in seconds."""
        with self._lock:
            total = sum(len(c) for c in self._chunks)
        return total / self._sr

    @staticmethod
    def list_devices() -> list[dict]:
        """Return a list of available audio input devices."""
        devices = sd.query_devices()
        inputs = []
        for i, d in enumerate(devices):
            if d["max_input_channels"] > 0:
                inputs.append({"index": i, "name": d["name"], "channels": d["max_input_channels"]})
        return inputs

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _audio_callback(
        self,
        indata: np.ndarray,
        frames: int,
        time_info: object,
        status: sd.CallbackFlags,
    ) -> None:
        if status:
            logger.warning("Audio callback status: %s", status)

        chunk = indata[:, 0].copy()  # mono float32
        with self._lock:
            self._chunks.append(chunk)

        if self._on_chunk is not None:
            try:
                self._on_chunk(chunk)
            except Exception:
                logger.exception("Error in on_chunk callback")
