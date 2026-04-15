"""Model download and management via huggingface_hub.

Models are stored under the project-local ./models/ directory.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable

logger = logging.getLogger(__name__)

KNOWN_MODELS: dict[str, str] = {
    "Qwen3-ASR-0.6B": "Qwen/Qwen3-ASR-0.6B",
    "Qwen3-ASR-1.7B": "Qwen/Qwen3-ASR-1.7B",
    "Qwen3-ForcedAligner-0.6B": "Qwen/Qwen3-ForcedAligner-0.6B",
}

ProgressCallback = Callable[[str, float], None]  # (status_text, 0.0‥1.0)


class ModelManager:
    """Manage local model downloads and availability checks."""

    def __init__(self, model_dir: str = "./models") -> None:
        self._model_dir = Path(model_dir)
        self._model_dir.mkdir(parents=True, exist_ok=True)

    @property
    def model_dir(self) -> Path:
        return self._model_dir

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def local_path(self, model_name: str) -> Path:
        return self._model_dir / model_name

    def is_downloaded(self, model_name: str) -> bool:
        path = self.local_path(model_name)
        if not path.is_dir():
            return False
        # Check for at least one .safetensors or .bin file
        has_weights = (
            list(path.glob("*.safetensors"))
            or list(path.glob("*.bin"))
            or list(path.glob("**/*.safetensors"))
            or list(path.glob("**/*.bin"))
        )
        return bool(has_weights)

    def list_downloaded(self) -> list[str]:
        return [name for name in KNOWN_MODELS if self.is_downloaded(name)]

    def list_available(self) -> list[str]:
        return list(KNOWN_MODELS.keys())

    # ------------------------------------------------------------------
    # Download
    # ------------------------------------------------------------------

    def download(
        self,
        model_name: str,
        progress_cb: ProgressCallback | None = None,
    ) -> Path:
        """Download a model from HuggingFace Hub to local_dir.

        Returns the local model path.
        """
        repo_id = KNOWN_MODELS.get(model_name)
        if repo_id is None:
            raise ValueError(
                f"Unknown model: {model_name}. "
                f"Available: {list(KNOWN_MODELS.keys())}"
            )

        dest = self.local_path(model_name)

        if self.is_downloaded(model_name):
            logger.info("Model %s already exists at %s", model_name, dest)
            if progress_cb:
                progress_cb(f"{model_name} 已存在", 1.0)
            return dest

        if progress_cb:
            progress_cb(f"正在下載 {model_name}…", 0.0)

        try:
            from huggingface_hub import snapshot_download

            snapshot_download(
                repo_id,
                local_dir=str(dest),
                resume_download=True,
            )
            logger.info("Model %s downloaded to %s", model_name, dest)
            if progress_cb:
                progress_cb(f"{model_name} 下載完成", 1.0)
        except Exception as exc:
            logger.error("Download failed for %s: %s", model_name, exc)
            if progress_cb:
                progress_cb(f"下載失敗: {exc}", -1.0)
            raise

        return dest

    def delete(self, model_name: str) -> None:
        """Remove a locally downloaded model."""
        import shutil

        path = self.local_path(model_name)
        if path.exists():
            shutil.rmtree(path)
            logger.info("Deleted model %s at %s", model_name, path)
