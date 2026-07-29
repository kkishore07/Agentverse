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


class MockLLMClient:
    """Fallback LLMClient used when local Ollama server is offline or unreachable."""

    def __init__(self, model: str = "qwen2.5-coder:3b") -> None:
        self._model = model

    async def is_reachable(self) -> bool:
        return False

    async def list_models(self) -> list[str]:
        return ["qwen2.5-coder:3b (mock)", "llama3 (mock)"]

    async def generate(
        self,
        prompt: str,
        *,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        json_mode: bool = False,
    ) -> LLMResponse:
        text = self._mock_response(prompt, system, json_mode)
        return LLMResponse(text=text, model=f"{self._model} (fallback)", duration_seconds=0.05)

    async def stream(
        self,
        prompt: str,
        *,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        json_mode: bool = False,
    ) -> AsyncIterator[str]:
        full_text = self._mock_response(prompt, system, json_mode)
        words = full_text.split(" ")
        for i, word in enumerate(words):
            yield word + (" " if i < len(words) - 1 else "")
            await asyncio.sleep(0.01)

    def _mock_response(self, prompt: str, system: Optional[str], json_mode: bool) -> str:
        p_lower = (prompt + " " + (system or "")).lower()

        if json_mode or "json" in p_lower:
            if "planner" in p_lower or "project" in p_lower or "tasks" in p_lower:
                return json.dumps({
                    "project": "devpilot_app",
                    "tasks": [
                        "Initialize application skeleton and configuration",
                        "Build core frontend user interface components",
                        "Implement backend routing and data models",
                        "Add interactive features and responsive styling",
                        "Write test suite and README documentation"
                    ]
                }, indent=2)

            if "architect" in p_lower or "folders" in p_lower or "manifest" in p_lower:
                return json.dumps({
                    "tech_stack": ["HTML5", "Vanilla CSS", "JavaScript"],
                    "folders": ["src"],
                    "files": [
                        {"path": "index.html", "purpose": "Main user interface template", "type": "code"},
                        {"path": "style.css", "purpose": "Application layout and visual styles", "type": "code"},
                        {"path": "script.js", "purpose": "Client interactivity and event logic", "type": "code"},
                        {"path": "README.md", "purpose": "Project documentation and usage instructions", "type": "docs"}
                    ]
                }, indent=2)

            if "coder" in p_lower or "write" in p_lower:
                if "index.html" in p_lower:
                    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>DevPilot App</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
  <div class="app">
    <h1>DevPilot Application</h1>
    <p>Scaffolded automatically by DevPilot AI.</p>
  </div>
  <script src="script.js"></script>
</body>
</html>"""
                elif "style.css" in p_lower:
                    return """body { margin: 0; font-family: system-ui, sans-serif; background: #0b0e14; color: #d7dce5; padding: 2rem; }
.app { max-width: 600px; margin: 0 auto; background: #11151d; padding: 2rem; border-radius: 8px; border: 1px solid #232a38; }"""
                elif "script.js" in p_lower:
                    return """console.log('DevPilot app active');"""
                else:
                    return "# DevPilot Generated Code\n"

            return json.dumps({"status": "ok", "message": "Simulated response"}, indent=2)

        return (
            "⚠️  **Notice**: Cannot reach local Ollama server at `http://localhost:11434`.\n\n"
            "To connect to a live local model:\n"
            "1. Install Ollama from [https://ollama.com](https://ollama.com)\n"
            "2. Run `ollama serve` in a terminal window\n"
            "3. Pull a model using `ollama pull qwen2.5-coder:3b`\n\n"
            "Operating in fallback mode for now. How can I help you with your project architecture or code structure?"
        )


class OllamaLLMClient:
    """Concrete LLMClient backed by a local Ollama server."""

    def __init__(
        self,
        host: str,
        model: str,
        timeout_seconds: int = 180,
        max_retries: int = 3,
        default_temperature: float = 0.2,
        enable_fallback: bool = True,
    ) -> None:
        self._host = host.rstrip("/")
        self._model = model
        self._timeout = timeout_seconds
        self._max_retries = max_retries
        self._default_temperature = default_temperature
        self._enable_fallback = enable_fallback
        self._mock = MockLLMClient(model=model)

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
                logger.warning("Cannot reach Ollama at %s (attempt %d/%d).", self._host, attempt, self._max_retries)
            except httpx.TimeoutException as exc:
                last_error = exc
                logger.warning("LLM request timed out (attempt %d/%d).", attempt, self._max_retries)
            except httpx.HTTPStatusError as exc:
                last_error = exc
                logger.warning("Ollama returned HTTP %s (attempt %d/%d).", exc.response.status_code, attempt, self._max_retries)
            except (json.JSONDecodeError, LLMError) as exc:
                last_error = exc
                logger.warning("Bad response from Ollama (attempt %d/%d): %s", attempt, self._max_retries, exc)

            if attempt < self._max_retries and not isinstance(last_error, (httpx.ConnectError, httpx.ConnectTimeout)):
                backoff = min(2 ** attempt, 10)
                await asyncio.sleep(backoff)

        if self._enable_fallback and isinstance(last_error, (httpx.ConnectError, httpx.ConnectTimeout)):
            logger.warning("Ollama unreachable. Falling back to MockLLMClient.")
            return await self._mock.generate(prompt, system=system, temperature=temperature, json_mode=json_mode)

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
            logger.warning("Cannot reach Ollama at %s. Falling back to MockLLMClient stream.", self._host)
            if self._enable_fallback:
                async for token in self._mock.stream(prompt, system=system, temperature=temperature, json_mode=json_mode):
                    yield token
            else:
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

