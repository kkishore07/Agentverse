"""
core/chat.py
============
ChatEngine: powers the default chat mode.

This is the direct LLM conversation layer — no agents, no orchestrator.
When the user types a question, greeting, or explanation request, this
handles it by streaming tokens directly from the LLM.
"""

from __future__ import annotations

from typing import AsyncIterator, Callable, Optional
from core.llm import OllamaLLMClient, LLMError

SYSTEM_PROMPT = """You are DevPilot, a professional AI coding assistant embedded in the terminal.

Your personality:
- Expert software engineer with deep knowledge across languages and frameworks
- Concise and clear — no padding, no unnecessary filler
- Helpful and direct — answer what was asked, then stop
- When showing code, always use proper formatting

You are running inside a user's project directory. You can help with:
- Answering technical questions and explaining concepts
- Reviewing code and suggesting improvements
- Debugging errors
- Planning software architecture
- Generating code on request

When the user asks you to CREATE, BUILD, or GENERATE something that requires
writing actual files, always clarify that you will write those files and what
you plan to do before starting.

Keep responses concise. Use markdown formatting when it helps clarity.
"""


class ChatEngine:
    """Stateful conversation engine using direct LLM streaming."""

    def __init__(self, llm: OllamaLLMClient) -> None:
        self._llm = llm
        self._history: list[dict] = []

    def add_user_message(self, text: str) -> None:
        self._history.append({"role": "user", "content": text})

    def add_assistant_message(self, text: str) -> None:
        self._history.append({"role": "assistant", "content": text})

    def clear_history(self) -> None:
        self._history.clear()

    def get_history(self) -> list[dict]:
        return list(self._history)

    def _build_prompt(self, user_message: str) -> str:
        """Build a single prompt string from conversation history."""
        parts = []
        for msg in self._history:
            role = msg["role"].capitalize()
            parts.append(f"{role}: {msg['content']}")
        parts.append(f"User: {user_message}")
        parts.append("Assistant:")
        return "\n\n".join(parts)

    async def respond_stream(
        self,
        user_message: str,
        on_token: Optional[Callable[[str], None]] = None,
    ) -> str:
        """
        Stream a response to user_message.

        Calls on_token(token) for each chunk as it arrives so the UI
        can render live output. Returns the complete assembled response.
        """
        prompt = self._build_prompt(user_message)
        full_response = ""

        try:
            async for token in self._llm.stream(prompt, system=SYSTEM_PROMPT):
                full_response += token
                if on_token:
                    on_token(token)
        except LLMError as exc:
            error_msg = f"\n[Error: {exc}]\n"
            full_response += error_msg
            if on_token:
                on_token(error_msg)

        # Store in history for context
        self.add_user_message(user_message)
        self.add_assistant_message(full_response)
        return full_response
