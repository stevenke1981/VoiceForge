"""LLM-based text polishing via Anthropic, OpenAI, or Google APIs.

Each provider is called through its official SDK.
API keys are read from the ConfigManager at call time.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

_DEFAULT_PROMPT = "請潤飾以下語音辨識文字，修正錯字、加標點符號，保持原意："


class LLMPolisher:
    """Unified interface for LLM polishing across providers."""

    def __init__(self, config: Any) -> None:
        """
        Args:
            config: A ConfigManager instance (or any object with .get(key)).
        """
        self._config = config

    def polish(
        self,
        text: str,
        provider: str | None = None,
        model: str | None = None,
        system_prompt: str | None = None,
    ) -> str:
        """Polish the given text using the configured LLM provider.

        Args:
            text: Raw transcription text.
            provider: "anthropic", "openai", or "google". Defaults to config value.
            model: Override model name.
            system_prompt: Override system/polishing prompt.

        Returns:
            Polished text string.

        Raises:
            ValueError: If provider is unknown or API key is missing.
            RuntimeError: If the API call fails.
        """
        provider = provider or self._config.get("llm_provider", "anthropic")
        prompt = system_prompt or self._config.get("polish_prompt", _DEFAULT_PROMPT)

        dispatch = {
            "anthropic": self._anthropic,
            "openai": self._openai,
            "google": self._google,
            "gemma": self._google,   # alias: gemma → google provider
        }

        handler = dispatch.get(provider)
        if handler is None:
            raise ValueError(f"Unknown LLM provider: {provider}. Use: {list(dispatch)}")

        return handler(text, prompt, model)

    # ------------------------------------------------------------------
    # Provider implementations
    # ------------------------------------------------------------------

    def _anthropic(self, text: str, prompt: str, model: str | None) -> str:
        api_key = self._config.get("anthropic_api_key", "")
        if not api_key:
            raise ValueError("Anthropic API key not configured")

        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        resolved_model = model or self._config.get("llm_model", "claude-sonnet-4-20250514")

        message = client.messages.create(
            model=resolved_model,
            max_tokens=4096,
            messages=[
                {"role": "user", "content": f"{prompt}\n\n{text}"},
            ],
        )
        return message.content[0].text

    def _openai(self, text: str, prompt: str, model: str | None) -> str:
        api_key = self._config.get("openai_api_key", "")
        if not api_key:
            raise ValueError("OpenAI API key not configured")

        import openai

        client = openai.OpenAI(api_key=api_key)
        resolved_model = model or "gpt-4o-mini"

        response = client.chat.completions.create(
            model=resolved_model,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": text},
            ],
            max_tokens=4096,
        )
        return response.choices[0].message.content or ""

    def _google(self, text: str, prompt: str, model: str | None) -> str:
        """Call Google AI via the google-genai SDK.

        Supports both Gemma and Gemini models.
        Default: gemma-4-26b-a4b-it (Gemma 4 MoE efficient variant).
        """
        api_key = self._config.get("google_api_key", "")
        if not api_key:
            raise ValueError("Google API key not configured")

        from google import genai
        from google.genai.types import GenerateContentConfig

        # Pass api_key directly; avoid setting env vars to prevent
        # "Both GOOGLE_API_KEY and GEMINI_API_KEY are set" warning.
        client = genai.Client(api_key=api_key)
        resolved_model = model or self._config.get("llm_model", "gemma-4-26b-a4b-it")

        response = client.models.generate_content(
            model=resolved_model,
            contents=f"{prompt}\n\n{text}",
            config=GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=2048,
                top_p=0.95,
            ),
        )
        return response.text or ""
