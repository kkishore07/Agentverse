"""
core/router.py
==============
IntentRouter: decides whether a user message is CHAT or TASK.

Classification is done in two stages:
  1. Fast heuristic pass (keyword matching) — no LLM call, instant
  2. If ambiguous, short LLM call to classify

CHAT  → Direct answer via ChatEngine
TASK  → Software engineering work → Orchestrator
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Optional


class Intent(Enum):
    CHAT = "chat"
    TASK = "task"


# Keywords that strongly indicate the user wants actual code generation / file work
_TASK_PATTERNS = [
    r"\b(create|build|generate|make|write|implement|add|setup|scaffold|init|initialize)\b",
    r"\b(update|modify|change|edit|refactor|rewrite|fix|debug|rename|delete|remove)\b",
    r"\b(refactor|rewrite|restructure|reorganize|rename|move)\b",
    r"\b(fix|debug|resolve|patch|repair)\s+(the\s+)?(\w+\s+)?(bug|error|issue|problem|crash|exception)\b",
    r"\b(add|create|write|generate)\s+(a\s+)?(test|spec|unit test|integration test)\b",
    r"\b(deploy|dockerize|containerize|publish|release)\b",
    r"\b(install|add)\s+(a\s+)?(package|dependency|library|module)\b",
    r"\b(create|add|generate|update|modify|change|rename)\s+(a\s+)?(class|function|method|endpoint|route|api|model|schema|migration|component|app|project|name)\b",
]

# Keywords that strongly indicate conversational / explanatory intent
_CHAT_PATTERNS = [
    r"^(hi|hello|hey|yo|sup|good\s+(morning|afternoon|evening))",
    r"\b(what\s+is|what\s+are|what\s+does|what\s+do)\b",
    r"\b(how\s+(does|do|can|should|would|to))\b",
    r"\b(explain|describe|tell\s+me|show\s+me|walk\s+me\s+through|help\s+me\s+understand)\b",
    r"\b(why\s+(is|are|does|do|did|would|should))\b",
    r"\b(difference\s+between|compare|vs\.?|versus)\b",
    r"\b(what('s|\s+is)\s+the\s+(best|difference|purpose|point|use|advantage|disadvantage))\b",
    r"\b(can\s+you\s+(explain|help|tell|show))\b",
    r"^(thanks|thank\s+you|thx|ty)\b",
    r"^(ok|okay|got\s+it|understood|makes\s+sense)",
]


def _compile(patterns: list[str]):
    return [re.compile(p, re.IGNORECASE) for p in patterns]


_TASK_REGEXES = _compile(_TASK_PATTERNS)
_CHAT_REGEXES = _compile(_CHAT_PATTERNS)


class IntentRouter:
    """Classifies user intent as CHAT or TASK using heuristics."""

    def classify(self, message: str, history: Optional[list] = None) -> Intent:
        """
        Return Intent.CHAT or Intent.TASK.

        Uses pure regex — no LLM call needed in the vast majority of cases.
        Falls back to CHAT (conservative) when ambiguous.
        """
        stripped = message.strip()
        if not stripped:
            return Intent.CHAT

        # Short inputs are almost always chat
        word_count = len(stripped.split())
        if word_count <= 1:
            return Intent.CHAT

        # Check CHAT patterns first (they're more precise)
        for pattern in _CHAT_REGEXES:
            if pattern.search(stripped):
                return Intent.CHAT

        # Check TASK patterns
        task_score = sum(1 for p in _TASK_REGEXES if p.search(stripped))
        if task_score >= 1:
            return Intent.TASK

        # Default: treat as CHAT (safe fallback — never surprise the user)
        return Intent.CHAT
