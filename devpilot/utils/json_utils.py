"""
utils/json_utils.py
====================
Small local models (like qwen2.5-coder:3b) frequently wrap JSON in
markdown fences, add a stray sentence before/after, or produce trailing
commas. This module centralizes "best-effort JSON extraction" so every
agent that needs structured output (Planner, Architect) doesn't
reimplement the same regex/cleanup logic.
"""

from __future__ import annotations

import json
import re
from typing import Any


class JSONExtractionError(Exception):
    """Raised when no valid JSON object/array could be extracted from text."""


def extract_json(raw_text: str) -> Any:
    """Best-effort extraction of a JSON value from LLM output.

    Strategy (cheapest first):
      1. Try parsing the raw text directly.
      2. Strip markdown code fences (```json ... ```) and retry.
      3. Find the first balanced {...} or [...] substring and retry.
      4. Give up and raise `JSONExtractionError`.

    Args:
        raw_text: The raw string returned by the LLM.

    Returns:
        The parsed Python object (dict or list).

    Raises:
        JSONExtractionError: if nothing parseable was found.
    """
    candidates = [raw_text.strip()]

    fenced = _strip_code_fences(raw_text)
    if fenced:
        candidates.append(fenced)

    balanced = _find_balanced_json(raw_text)
    if balanced:
        candidates.append(balanced)

    for candidate in candidates:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            cleaned = _remove_trailing_commas(candidate)
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError:
                continue

    raise JSONExtractionError(
        f"Could not extract valid JSON from LLM output. First 200 chars: {raw_text[:200]!r}"
    )


def _strip_code_fences(text: str) -> str | None:
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    return match.group(1).strip() if match else None


def _find_balanced_json(text: str) -> str | None:
    """Scan for the first balanced {...} or [...] block, tracking string
    state so braces inside string literals don't throw off the count."""
    for open_ch, close_ch in (("{", "}"), ("[", "]")):
        start = text.find(open_ch)
        if start == -1:
            continue
        depth = 0
        in_string = False
        escape = False
        for i in range(start, len(text)):
            ch = text[i]
            if in_string:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == '"':
                    in_string = False
                continue
            if ch == '"':
                in_string = True
            elif ch == open_ch:
                depth += 1
            elif ch == close_ch:
                depth -= 1
                if depth == 0:
                    return text[start : i + 1]
    return None


def _remove_trailing_commas(text: str) -> str:
    return re.sub(r",\s*([}\]])", r"\1", text)
