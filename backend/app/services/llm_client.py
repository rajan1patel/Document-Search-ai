"""
Lightweight OpenAI-compatible LLM client for the Expert Discovery Pipeline.

Uses OpenRouter under the hood (configurable via settings).
Separate from DSPy — this is a direct HTTP client for structured JSON extraction.
"""
import json
import logging
from typing import Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMClient:
    """Minimal OpenAI-compatible client for structured extraction tasks."""

    def __init__(self):
        self.api_key: str = settings.OPENROUTER_API_KEY
        self.base_url: str = settings.LLM_BASE_URL.rstrip("/")
        self.model: str = settings.LLM_MODEL
        self.max_tokens: int = settings.LLM_MAX_TOKENS
        self.temperature: float = settings.LLM_TEMPERATURE
        self.timeout: int = settings.LLM_TIMEOUT

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        response_format: Optional[dict] = None,
    ) -> str:
        """
        Send a chat completion request and return the text content.

        If response_format={"type": "json_object"} is passed, the model is
        instructed to return valid JSON (and we validate it).
        """
        if not self.api_key:
            raise RuntimeError(
                "OPENROUTER_API_KEY is not set. "
                "Add a valid OpenRouter API key to the .env file."
            )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        body: dict = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }

        if response_format:
            body["response_format"] = response_format

        logger.info(
            "LLM call: model=%s | system=%s… | user=%s…",
            self.model, system_prompt[:80], user_prompt[:80],
        )

        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self._headers(),
                    json=body,
                )
                resp.raise_for_status()
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                logger.info("LLM response received (%d chars)", len(content))
                return content
        except httpx.HTTPStatusError as exc:
            logger.error("LLM HTTP error: %s - %s", exc, exc.response.text[:500])
            raise
        except Exception as exc:
            logger.error("LLM call failed: %s", exc, exc_info=True)
            raise

    def extract_json(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> dict:
        """
        Convenience method: ask the LLM for JSON, parse and return it.
        The system prompt should instruct the model to return valid JSON.
        """
        raw = self.chat(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_format={"type": "json_object"},
        )
        # Strip code fences if present
        raw = raw.strip()
        if raw.startswith("```"):
            # Remove ```json ... ``` fences
            lines = raw.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            raw = "\n".join(lines).strip()
        return json.loads(raw)


# Singleton
llm_client = LLMClient()
