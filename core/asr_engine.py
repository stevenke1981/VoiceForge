"""Qwen3-ASR engine wrapper.

Uses the qwen-asr PyPI package (NOT raw transformers) for inference.
Models are loaded from the local ./models/ directory.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TranscriptionResult:
    text: str
    language: str | None = None
    timestamps: list[dict[str, Any]] | None = None


class ASREngine:
    """Wrapper around Qwen3ASRModel from the qwen-asr package."""

    def __init__(self) -> None:
        self._model: Any | None = None
        self._model_name: str = ""
        self._device: str = "cpu"

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    @property
    def current_model(self) -> str:
        return self._model_name

    def load(
        self,
        model_path: str | Path,
        device: str = "auto",
        max_new_tokens: int = 256,
    ) -> None:
        """Load a Qwen3-ASR model from a local directory.

        Args:
            model_path: Path to the local model directory (e.g. ./models/Qwen3-ASR-0.6B).
            device: "auto", "cuda:0", or "cpu".
            max_new_tokens: Maximum tokens for generation.
        """
        import torch
        from qwen_asr import Qwen3ASRModel

        model_path = Path(model_path)
        if not model_path.exists():
            raise FileNotFoundError(f"Model path not found: {model_path}")

        resolved_device = self._resolve_device(device)
        dtype = torch.float16 if "cuda" in resolved_device else torch.float32

        logger.info(
            "Loading ASR model from %s (device=%s, dtype=%s)",
            model_path, resolved_device, dtype,
        )

        # device_map triggers accelerate's meta-tensor dispatch, which breaks on CPU.
        # Only pass device_map for CUDA. For CPU, disable low_cpu_mem_usage so
        # transformers loads weights directly without creating meta tensors.
        load_kwargs: dict = {"dtype": dtype, "max_new_tokens": max_new_tokens}
        if resolved_device.startswith("cuda"):
            load_kwargs["device_map"] = resolved_device
        else:
            load_kwargs["low_cpu_mem_usage"] = False

        self._model = Qwen3ASRModel.from_pretrained(str(model_path), **load_kwargs)

        # Reload GenerationConfig from disk so all special-token IDs are plain
        # Python integers rather than meta-device tensors that transformers
        # may have created during model initialisation. Without this fix,
        # model.generate() raises "Tensor.item() cannot be called on meta tensors".
        if not resolved_device.startswith("cuda"):
            self._fix_generation_config(model_path)

        self._model_name = model_path.name
        self._device = resolved_device
        logger.info("ASR model loaded: %s", self._model_name)

    def unload(self) -> None:
        """Release model from memory."""
        if self._model is not None:
            del self._model
            self._model = None
            self._model_name = ""
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            logger.info("ASR model unloaded")

    def transcribe(
        self,
        audio: str | Path | tuple[np.ndarray, int],
        language: str | None = None,
        return_timestamps: bool = False,
    ) -> TranscriptionResult:
        """Transcribe audio input.

        Args:
            audio: File path, or (ndarray, sample_rate) tuple.
            language: ISO language code or None for auto-detect.
            return_timestamps: Whether to return word-level timestamps.

        Returns:
            TranscriptionResult with text, detected language, and optional timestamps.
        """
        if not self.is_loaded:
            raise RuntimeError("No model loaded. Call load() first.")

        # Prepare audio input
        if isinstance(audio, (str, Path)):
            audio_input = str(audio)
        else:
            audio_input = audio  # (ndarray, sr) tuple

        raw = self._model.transcribe(
            audio=audio_input,
            language=language,
            return_time_stamps=return_timestamps,
        )

        # qwen-asr may return a list even for a single input
        if isinstance(raw, list):
            raw = raw[0]

        return TranscriptionResult(
            text=raw.text,
            language=getattr(raw, "language", None),
            timestamps=getattr(raw, "time_stamps", None),
        )

    def transcribe_batch(
        self,
        audio_list: list[str | Path | tuple[np.ndarray, int]],
        language: str | None = None,
        return_timestamps: bool = False,
    ) -> list[TranscriptionResult]:
        """Batch transcribe multiple audio inputs."""
        if not self.is_loaded:
            raise RuntimeError("No model loaded. Call load() first.")

        inputs = []
        for a in audio_list:
            if isinstance(a, (str, Path)):
                inputs.append(str(a))
            else:
                inputs.append(a)

        languages = [language] * len(inputs) if language else [None] * len(inputs)

        results = self._model.transcribe(
            audio=inputs,
            language=languages,
            return_time_stamps=return_timestamps,
        )

        # Handle single vs batch result
        if not isinstance(results, list):
            results = [results]

        return [
            TranscriptionResult(
                text=r.text,
                language=getattr(r, "language", None),
                timestamps=getattr(r, "time_stamps", None),
            )
            for r in results
        ]

    def _fix_generation_config(self, model_path: Path) -> None:
        """Fix GenerationConfig issues caused by CPU loading.

        Two problems addressed:
        1. Meta-device tensors: transformers may store special-token IDs
           (eos, pad, bos) as meta tensors during init; reloading from disk
           gives plain integers that generate() can handle.
        2. Invalid generation flags: if the config has temperature != 1.0
           but do_sample=False, transformers warns "generation flags are not
           valid". Resetting temperature to the default (1.0) suppresses it.
        """
        try:
            from transformers import GenerationConfig
            clean_cfg = GenerationConfig.from_pretrained(str(model_path))

            # Reset temperature to default so it isn't flagged as an
            # incompatible param when greedy / beam-search decoding is used.
            if not getattr(clean_cfg, "do_sample", False):
                clean_cfg.temperature = 1.0

            inner = getattr(self._model, "model", None)
            if inner is not None and hasattr(inner, "generation_config"):
                inner.generation_config = clean_cfg
                logger.debug("GenerationConfig reloaded and patched from disk")
        except Exception as exc:
            logger.warning("Could not reload GenerationConfig: %s", exc)

    @staticmethod
    def _resolve_device(device: str) -> str:
        import torch
        if device == "auto":
            if torch.cuda.is_available():
                return "cuda:0"
            logger.warning("CUDA 不可用，自動降回 CPU")
            return "cpu"
        if device.startswith("cuda") and not torch.cuda.is_available():
            raise RuntimeError(
                f"裝置 '{device}' 不可用：找不到 CUDA GPU。"
                " 請確認 NVIDIA 驅動與 CUDA 已正確安裝，或在設定中改為 'auto' / 'cpu'。"
            )
        return device
