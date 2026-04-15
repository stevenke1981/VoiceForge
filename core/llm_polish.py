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
        api_key = self._config.get("google_api_key", "")
        if not api_key:
            raise ValueError("Google API key not configured")

        import google.generativeai as genai

        genai.configure(api_key=api_key)
        resolved_model = model or "gemini-2.0-flash"

        gen_model = genai.GenerativeModel(resolved_model)
        response = gen_model.generate_content(f"{prompt}\n\n{text}")
        return response.text or ""
