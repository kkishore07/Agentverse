"""
agents/fixer.py
===============
Fixer Agent that takes a file with validation or test errors,
and rewrites the file to fix those errors.
"""

from __future__ import annotations

from dataclasses import dataclass
from agents.base import Agent, AgentError
from agents.coder import _strip_stray_fences
from core.prompts import fixer_prompt


@dataclass(frozen=True)
class FixerInput:
    file_path: str
    content: str
    errors: list[str]


@dataclass(frozen=True)
class FixerOutput:
    file_path: str
    fixed_content: str


class FixerAgent(Agent[FixerInput, FixerOutput]):
    """Analyzes validation or test errors in a file and attempts to fix them."""

    name = "fixer"

    async def run(self, agent_input: FixerInput) -> FixerOutput:
        system, user = fixer_prompt(
            file_path=agent_input.file_path,
            content=agent_input.content,
            errors=agent_input.errors,
        )
        
        response = await self._llm.generate(user, system=system)
        
        content = _strip_stray_fences(response.text)
        if not content.strip():
            raise AgentError(f"FixerAgent: generated empty content for {agent_input.file_path}")

        return FixerOutput(
            file_path=agent_input.file_path,
            fixed_content=content
        )
