"""
core/llm.py
===========
LLM abstraction layer. Supports both single-shot generation and streaming.

Streaming is used by the ChatEngine so tokens appear live in the terminal.
Single-shot is kept for agents that need a complete JSON response.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from typing import AsyncIterator, Optional, Protocol

import asyncio
import httpx

logger = logging.getLogger("devpilot.llm")


class LLMError(Exception):
    """Raised when the LLM layer cannot produce a usable response."""


@dataclass(frozen=True)
class LLMResponse:
    """Normalized response returned by single-shot generation."""
    text: str
    model: str
    duration_seconds: float


class LLMClient(Protocol):
    """Interface every LLM backend must satisfy."""

    async def generate(
        self,
        prompt: str,
        *,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        json_mode: bool = False,
    ) -> LLMResponse: ...

    async def stream(
        self,
        prompt: str,
        *,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        json_mode: bool = False,
    ) -> AsyncIterator[str]: ...


class OllamaLLMClient:
    """Concrete LLMClient backed by a local Ollama server."""

    def __init__(
        self,
        host: str,
        model: str,
        timeout_seconds: int = 180,
        max_retries: int = 3,
        default_temperature: float = 0.2,
    ) -> None:
        self._host = host.rstrip("/")
        self._model = model
        self._timeout = timeout_seconds
        self._max_retries = max_retries
        self._default_temperature = default_temperature

    async def generate(
        self,
        prompt: str,
        *,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        json_mode: bool = False,
    ) -> LLMResponse:
        """Single-shot generation with retries (used by agents)."""
        payload = {
            "model": self._model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature if temperature is not None else self._default_temperature,
            },
        }
        if system:
            payload["system"] = system
        if json_mode:
            payload["format"] = "json"

        last_error: Optional[Exception] = None
        for attempt in range(1, self._max_retries + 1):
            start = time.monotonic()
            try:
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    resp = await client.post(f"{self._host}/api/generate", json=payload)
                    resp.raise_for_status()
                    data = resp.json()
                duration = time.monotonic() - start
                text = data.get("response", "")
                if not text.strip():
                    raise LLMError("Ollama returned an empty response.")
                return LLMResponse(text=text, model=self._model, duration_seconds=duration)

            except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
                last_error = exc
                logger.error("Cannot reach Ollama at %s (attempt %d/%d).", self._host, attempt, self._max_retries)
            except httpx.TimeoutException as exc:
                last_error = exc
                logger.warning("LLM request timed out (attempt %d/%d).", attempt, self._max_retries)
            except httpx.HTTPStatusError as exc:
                last_error = exc
                logger.warning("Ollama returned HTTP %s (attempt %d/%d).", exc.response.status_code, attempt, self._max_retries)
            except (json.JSONDecodeError, LLMError) as exc:
                last_error = exc
                logger.warning("Bad response from Ollama (attempt %d/%d): %s", attempt, self._max_retries, exc)

            if attempt < self._max_retries:
                backoff = min(2 ** attempt, 10)
                await asyncio.sleep(backoff)

        raise LLMError(f"LLM generation failed after {self._max_retries} attempts. Last error: {last_error}")

    async def stream(
        self,
        prompt: str,
        *,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        json_mode: bool = False,
    ) -> AsyncIterator[str]:
        """Streaming generation — yields tokens as they arrive (used by ChatEngine)."""
        payload = {
            "model": self._model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": temperature if temperature is not None else self._default_temperature,
            },
        }
        if system:
            payload["system"] = system
        if json_mode:
            payload["format"] = "json"

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                async with client.stream("POST", f"{self._host}/api/generate", json=payload) as resp:
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        if not line.strip():
                            continue
                        try:
                            data = json.loads(line)
                            token = data.get("response", "")
                            if token:
                                yield token
                            if data.get("done", False):
                                break
                        except json.JSONDecodeError:
                            continue
        except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
            raise LLMError(f"Cannot reach Ollama: {exc}") from exc
        except httpx.HTTPStatusError as exc:
            raise LLMError(f"Ollama HTTP error {exc.response.status_code}") from exc

    # ---- Model management helpers ----

    async def list_models(self) -> list[str]:
        """Return a list of locally installed Ollama model names."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{self._host}/api/tags")
                resp.raise_for_status()
                data = resp.json()
                return [m["name"] for m in data.get("models", [])]
        except Exception:
            return []

    async def is_reachable(self) -> bool:
        """Check whether Ollama is running and reachable."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{self._host}/api/tags")
                return resp.status_code == 200
        except Exception:
            return False


def build_default_llm_client(settings) -> OllamaLLMClient:
    return OllamaLLMClient(
        host=settings.ollama_host,
        model=settings.model_name,
        timeout_seconds=settings.llm_timeout_seconds,
        max_retries=settings.llm_max_retries,
        default_temperature=settings.llm_temperature,
    )
