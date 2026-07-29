"""
agents/architect.py
====================
Receives the Planner's output and designs the concrete project
structure: tech stack, folders, and a file manifest (each file with a
one-sentence purpose and a type tag: "code" | "test" | "docs").

The Orchestrator uses `ArchitectOutput.files` to drive the per-file loop
that follows (Coder -> Tester -> Docs), so this agent's job is really
"produce the plan the rest of the pipeline iterates over."
"""

from __future__ import annotations

from dataclasses import dataclass, field

from agents.base import Agent, AgentError
from core.prompts import architect_prompt
from utils.json_utils import JSONExtractionError, extract_json


@dataclass(frozen=True)
class ArchitectInput:
    goal: str
    tasks: list[str]
    max_files: int = 40


@dataclass(frozen=True)
class FileSpec:
    path: str
    purpose: str
    type: str  # "code" | "test" | "docs"


@dataclass(frozen=True)
class ArchitectOutput:
    tech_stack: list[str] = field(default_factory=list)
    folders: list[str] = field(default_factory=list)
    files: list[FileSpec] = field(default_factory=list)


_VALID_TYPES = {"code", "test", "docs"}


class ArchitectAgent(Agent[ArchitectInput, ArchitectOutput]):
    """Designs folder structure, tech stack, and the file manifest."""

    name = "architect"

    async def run(self, agent_input: ArchitectInput) -> ArchitectOutput:
        self.emit_progress(current_milestone="Designing architecture", folder_structure="Pending", chosen_framework="Pending")
        
        system, user = architect_prompt(agent_input.goal, agent_input.tasks, agent_input.max_files)
        
        full_text = ""
        try:
            stream = self._llm.stream(user, system=system, json_mode=True)
            async for chunk in stream:
                full_text += chunk
                self.emit_progress(llm_token=chunk)
        except Exception as e:
            raise AgentError(f"Architect: LLM stream failed: {e}")

        self.emit_progress(current_milestone="Finalizing design")

        try:
            data = extract_json(full_text)
        except JSONExtractionError as exc:
            raise AgentError(f"Architect: could not parse LLM output as JSON: {exc}") from exc

        if not isinstance(data, dict):
            raise AgentError("Architect: expected a JSON object.")

        tech_stack = [str(x) for x in data.get("tech_stack", []) if str(x).strip()]
        folders = [str(x).strip("/") for x in data.get("folders", []) if str(x).strip()]

        raw_files = data.get("files")
        if not isinstance(raw_files, list) or not raw_files:
            raise AgentError("Architect: 'files' must be a non-empty list.")

        files: list[FileSpec] = []
        seen_paths: set[str] = set()
        for entry in raw_files[: agent_input.max_files]:
            if not isinstance(entry, dict):
                continue
            path = str(entry.get("path", "")).strip().lstrip("/")
            if not path or ".." in path.split("/"):
                continue
            if path in seen_paths:
                continue
            purpose = str(entry.get("purpose", "")).strip()
            file_type = str(entry.get("type", "code")).strip().lower()
            if file_type not in _VALID_TYPES:
                file_type = "code"
            files.append(FileSpec(path=path, purpose=purpose, type=file_type))
            seen_paths.add(path)

        if not files:
            raise AgentError("Architect: no valid file paths after sanitization.")

        # Guarantee a README exists even if the model forgot it.
        if not any(f.type == "docs" or f.path.upper() == "README.MD" for f in files):
            files.append(FileSpec(path="README.md", purpose="Project documentation.", type="docs"))

        return ArchitectOutput(tech_stack=tech_stack, folders=folders, files=files)
