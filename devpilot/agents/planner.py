"""
agents/planner.py
==================
Turns a free-form project request ("Build a FastAPI Todo Application")
into a structured plan: a project name and an ordered list of tasks.

This is the first agent in the pipeline. Its output feeds the Architect,
which relies on `PlannerOutput.tasks` to design the file structure.
"""

from __future__ import annotations

from typing import Any
from dataclasses import dataclass, field

from agents.base import Agent, AgentError
from core.prompts import planner_prompt
from utils.json_utils import JSONExtractionError, extract_json


@dataclass(frozen=True)
class PlannerInput:
    goal: str
    context_files: list[Any] = field(default_factory=list)


@dataclass(frozen=True)
class PlannerOutput:
    project_name: str
    tasks: list[str] = field(default_factory=list)


class PlannerAgent(Agent[PlannerInput, PlannerOutput]):
    """Understands the user's request and breaks it into ordered tasks."""

    name = "planner"

    async def run(self, agent_input: PlannerInput) -> PlannerOutput:
        self.emit_progress(current_milestone="Thinking about project requirements", progress="0%", current_reasoning="")
        
        system, user = planner_prompt(agent_input.goal)
        
        # Stream the LLM response to provide live reasoning in the UI
        full_text = ""
        try:
            stream = self._llm.stream(user, system=system, json_mode=True)
            async for chunk in stream:
                full_text += chunk
                self.emit_progress(llm_token=chunk)
        except Exception as e:
            raise AgentError(f"Planner: LLM stream failed: {e}")

        self.emit_progress(current_milestone="Parsing structured plan", progress="90%")

        try:
            data = extract_json(full_text)
        except JSONExtractionError as exc:
            raise AgentError(f"Planner: could not parse LLM output as JSON: {exc}") from exc

        if not isinstance(data, dict):
            raise AgentError("Planner: expected a JSON object with 'project' and 'tasks'.")

        project_name = str(data.get("project") or agent_input.goal).strip()
        tasks = data.get("tasks")
        if not isinstance(tasks, list) or not tasks:
            raise AgentError("Planner: 'tasks' must be a non-empty list.")

        cleaned_tasks = [str(t).strip() for t in tasks if str(t).strip()]
        if not cleaned_tasks:
            raise AgentError("Planner: no usable tasks after cleaning LLM output.")

        self.emit_progress(current_milestone="Done", progress="100%", estimated_completion="0s")
        return PlannerOutput(project_name=project_name, tasks=cleaned_tasks)
