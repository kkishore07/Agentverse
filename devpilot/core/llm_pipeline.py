"""
core/llm_pipeline.py
=====================
The full modular LLM pipeline:

  Agent → PromptEngine → PromptOptimizer → ModelRouter → LLM → OutputValidator → RetryEngine → Structured Output

Each stage is a separate, replaceable component.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Callable, Optional, Type, TypeVar

from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


# ─────────────────────────────────────────────────────────────
# PromptOptimizer
# ─────────────────────────────────────────────────────────────

class PromptOptimizer:
    """
    Optimizes a PromptBundle for a given model's context limit.

    Currently a lightweight implementation that truncates user_prompt
    if the estimated token count exceeds the model's max. Future
    versions can use tiktoken for precise measurement and smarter
    section-level trimming.
    """

    # Rough char-to-token ratio (conservative)
    CHARS_PER_TOKEN = 3.5

    def __init__(self, max_tokens: int = 6_000):
        self.max_tokens = max_tokens

    def optimize(self, system_prompt: str, user_prompt: str) -> tuple[str, str]:
        total_chars = len(system_prompt) + len(user_prompt)
        total_tokens_est = int(total_chars / self.CHARS_PER_TOKEN)

        if total_tokens_est <= self.max_tokens:
            return system_prompt, user_prompt

        # How many chars are we over budget?
        budget_chars = int(self.max_tokens * self.CHARS_PER_TOKEN)
        system_chars = len(system_prompt)
        allowed_user_chars = max(budget_chars - system_chars, 500)

        if len(user_prompt) > allowed_user_chars:
            logger.warning(
                "PromptOptimizer: user_prompt truncated from %d to %d chars to fit token budget.",
                len(user_prompt),
                allowed_user_chars,
            )
            user_prompt = (
                user_prompt[:allowed_user_chars]
                + "\n\n... [context truncated by PromptOptimizer to fit token budget]"
            )

        return system_prompt, user_prompt


# ─────────────────────────────────────────────────────────────
# ModelRouter
# ─────────────────────────────────────────────────────────────

class ModelRouter:
    """
    Selects the appropriate LLM client for a given agent and task type.

    Currently routes everything through the primary LLM. The architecture
    is prepared for multi-model routing (e.g., a faster model for short
    tasks, a smarter model for architectural decisions).
    """

    def __init__(self, primary_llm, fallback_llm=None):
        self._primary = primary_llm
        self._fallback = fallback_llm

    def route(self, agent_name: str, task_type: str = "default"):
        """Return the appropriate LLM client for the given agent."""
        # Future: route to different models based on agent_name/task_type
        return self._primary


# ─────────────────────────────────────────────────────────────
# OutputValidator
# ─────────────────────────────────────────────────────────────

class OutputValidator:
    """
    Validates raw LLM text output against a Pydantic schema.
    Returns (parsed_object, None) on success, (None, error_message) on failure.
    """

    @staticmethod
    def validate(response_text: str, schema_class: Type[T]) -> tuple[Optional[T], Optional[str]]:
        try:
            from utils.json_utils import extract_json  # type: ignore[import]
            data = extract_json(response_text)
        except Exception as e:
            return None, f"JSON extraction failed: {e}\n\nRaw output:\n{response_text[:500]}"

        try:
            parsed = schema_class.model_validate(data)
            return parsed, None
        except ValidationError as e:
            return None, f"Schema validation failed:\n{e}\n\nRaw output:\n{response_text[:500]}"
        except Exception as e:
            return None, f"Unexpected parse error: {e}"


# ─────────────────────────────────────────────────────────────
# RetryEngine
# ─────────────────────────────────────────────────────────────

REPAIR_INSTRUCTION = """
---
## REPAIR INSTRUCTION
Your previous response failed validation with the following error:

{error}

Please carefully re-read the OUTPUT SCHEMA and try again. Respond ONLY with valid JSON
that strictly matches the required schema. Do not include any prose, markdown fences,
or explanation outside the JSON object.
""".strip()


class RetryEngine:
    """
    Executes an LLM call with automatic retry on schema validation failure.

    On each failure, a REPAIR INSTRUCTION is appended to the user prompt
    with the exact validation error, giving the model the information it
    needs to self-correct.
    """

    def __init__(self, llm_client, max_retries: int = 2):
        self._llm = llm_client
        self.max_retries = max_retries

    async def execute_with_retry(
        self,
        system_prompt: str,
        user_prompt: str,
        schema_class: Type[T],
        token_callback: Optional[Callable[[str], None]] = None,
    ) -> T:
        """
        Calls the LLM, validates the output, and retries up to max_retries times.

        Args:
            system_prompt:   The assembled system prompt.
            user_prompt:     The assembled user prompt.
            schema_class:    The Pydantic model class to validate against.
            token_callback:  Optional callback for streaming tokens to the UI.
        """
        current_user_prompt = user_prompt
        last_error: Optional[str] = None

        for attempt in range(self.max_retries + 1):
            if attempt > 0:
                logger.warning("RetryEngine: Attempt %d/%d for %s", attempt + 1, self.max_retries + 1, schema_class.__name__)

            # ── Fast path: native structured output ────────────────────
            if hasattr(self._llm, "chat_structured"):
                try:
                    result = await self._llm.chat_structured(
                        [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": current_user_prompt},
                        ],
                        schema_class,
                    )
                    if result:
                        return result
                except Exception as e:
                    logger.debug("chat_structured failed: %s — falling back to stream", e)

            # ── Stream path: collect tokens then validate ──────────────
            full_text = ""
            try:
                stream = self._llm.stream(current_user_prompt, system=system_prompt, json_mode=True)
                async for chunk in stream:
                    full_text += chunk
                    if token_callback:
                        token_callback(chunk)
            except Exception as e:
                last_error = f"LLM stream error: {e}"
                logger.error("RetryEngine: LLM stream failed on attempt %d: %s", attempt + 1, e)
                if attempt >= self.max_retries:
                    raise RuntimeError(f"LLM stream failed after {self.max_retries + 1} attempts: {last_error}")
                continue

            parsed, error = OutputValidator.validate(full_text, schema_class)

            if parsed:
                return parsed

            last_error = error
            logger.warning("RetryEngine: Validation failed on attempt %d: %s", attempt + 1, error)

            if attempt < self.max_retries:
                # Append a repair instruction for the next attempt
                current_user_prompt = (
                    user_prompt
                    + "\n\n"
                    + REPAIR_INSTRUCTION.format(error=error)
                )

        raise ValueError(
            f"RetryEngine: Max retries ({self.max_retries}) exceeded for {schema_class.__name__}.\n"
            f"Final error: {last_error}"
        )
