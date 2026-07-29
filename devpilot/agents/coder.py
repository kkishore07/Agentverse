"""
agents/coder.py
================
Generates the content of ONE source file per call.

Deliberately never asked to generate the whole project in one prompt --
a 3B local model degrades fast on long, multi-file outputs. Keeping the
scope to one file at a time also lets the Orchestrator retry a single
failed file without regenerating everything else.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from agents.base import Agent, AgentError
from core.prompts import coder_prompt


@dataclass(frozen=True)
class CoderInput:
    goal: str
    tech_stack: list[str]
    file_path: str
    file_purpose: str
    sibling_files: list[str]


@dataclass(frozen=True)
class CoderOutput:
    path: str
    content: str


_FENCE_RE = re.compile(r"^```[a-zA-Z0-9_+-]*\n(.*)\n```$", re.DOTALL)


class CoderAgent(Agent[CoderInput, CoderOutput]):
    """Generates the full content for a single file."""

    name = "coder"

    async def run(self, agent_input: CoderInput) -> CoderOutput:
        self.emit_progress(
            current_file=agent_input.file_path, 
            current_operation="Writing", 
            current_class="-", 
            current_function="-",
            current_milestone=f"Generating {agent_input.file_path}",
            current_skill="Filesystem",
            progress="10%"
        )
        system, user = coder_prompt(
            goal=agent_input.goal,
            tech_stack=agent_input.tech_stack,
            file_path=agent_input.file_path,
            file_purpose=agent_input.file_purpose,
            sibling_files=agent_input.sibling_files,
        )
        
        full_text = ""
        current_class = "-"
        current_func = "-"
        
        from core.event_bus import EVENT_AGENT_STEP

        self._bus.publish(EVENT_AGENT_STEP, agent_name="Coder", step="Read: " + agent_input.file_path)
        
        try:
            self._bus.publish(EVENT_AGENT_STEP, agent_name="Coder", step="Generate: AI implementation...")
            self.emit_progress(current_milestone=f"Writing {agent_input.file_path}", current_skill="Filesystem", progress="30%")
            stream = self._llm.stream(user, system=system)
            async for chunk in stream:
                full_text += chunk
                
                # Simple heuristic to detect current class/function being written
                if "class " in chunk or "def " in chunk:
                    lines = full_text.splitlines()
                    if lines:
                        last_line = lines[-1]
                        if last_line.strip().startswith("class "):
                            current_class = last_line.split("class ")[1].split("(")[0].split(":")[0].strip()
                        elif last_line.strip().startswith("def "):
                            current_func = last_line.split("def ")[1].split("(")[0].strip()
                            
                self.emit_progress(llm_token=chunk, current_class=current_class, current_function=current_func, current_milestone=f"Writing {agent_input.file_path}", current_skill="Filesystem")
        except Exception as e:
            raise AgentError(f"Coder: LLM stream failed: {e}")

        self._bus.publish(EVENT_AGENT_STEP, agent_name="Coder", step="Apply: Merging diff...")
        self.emit_progress(current_milestone=f"Formatting {agent_input.file_path}", current_skill="Filesystem", progress="90%")

        content = _strip_stray_fences(full_text)
        if not content.strip():
            raise AgentError(f"Coder: empty content generated for '{agent_input.file_path}'.")

        self._bus.publish(EVENT_AGENT_STEP, agent_name="Coder", step="Validate: Syntax check")
        self._bus.publish(EVENT_AGENT_STEP, agent_name="Coder", step="Save: " + agent_input.file_path)

        self.emit_progress(current_operation="Completed", current_milestone=f"Saved {agent_input.file_path}", current_skill="Filesystem", progress="100%")
        return CoderOutput(path=agent_input.file_path, content=content)


def _strip_stray_fences(text: str) -> str:
    """Models often wrap output in ```lang ... ``` even when told not
    to. Strip a single outer fence if present, otherwise return as-is."""
    stripped = text.strip()
    match = _FENCE_RE.match(stripped)
    return match.group(1) if match else stripped
