"""
agents/docs.py
===============
Generates project documentation (README.md) once all code/test files
are known, so it can accurately describe the final file layout.
"""

from __future__ import annotations

from dataclasses import dataclass

from agents.base import Agent, AgentError
from agents.coder import _strip_stray_fences
from core.prompts import docs_prompt


@dataclass(frozen=True)
class DocsInput:
    goal: str
    tech_stack: list[str]
    files: list[dict]  # [{"path": ..., "purpose": ...}, ...]


@dataclass(frozen=True)
class DocsOutput:
    path: str
    content: str


class DocumentationAgent(Agent[DocsInput, DocsOutput]):
    """Generates a README describing the generated project."""

    name = "docs"

    async def run(self, agent_input: DocsInput) -> DocsOutput:
        self.emit_progress(readme_update="Writing", api_docs="Scanning", usage_examples="Pending", current_milestone="Writing README", current_skill="Documentation", progress="0%")
        system, user = docs_prompt(
            goal=agent_input.goal,
            tech_stack=agent_input.tech_stack,
            files=agent_input.files,
        )
        
        full_text = ""
        try:
            stream = self._llm.stream(user, system=system)
            async for chunk in stream:
                full_text += chunk
                self.emit_progress(llm_token=chunk, current_milestone="Writing README", current_skill="Documentation", progress="50%")
        except Exception as e:
            raise AgentError(f"DocumentationAgent: LLM stream failed: {e}")

        content = _strip_stray_fences(full_text)
        if not content.strip():
            raise AgentError("DocumentationAgent: empty README content generated.")

        self.emit_progress(readme_update="Complete", api_docs="Complete", usage_examples="Complete", current_milestone="Documentation Complete", current_skill="Documentation", progress="100%")
        return DocsOutput(path="README.md", content=content)
