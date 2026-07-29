"""
core/memory.py
==============
Lightweight, in-process "memory" for a single DevPilot run.

Deliberately NOT a vector database or a persistence layer -- just a
typed container the Orchestrator threads through the pipeline so every
agent (and the Project Writer, and CLI introspection commands) can see
what's happened so far: the goal, the plan, the architecture, and every
file generated.

Optionally dumped to `logs/` as JSON at the end of a run for debugging
and for `devpilot explain` / `devpilot improve` to load back later.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


@dataclass
class GeneratedFile:
    """Record of a single generated source file."""

    path: str
    purpose: str = ""
    content: str = ""
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class ProjectMemory:
    """The full state of one `devpilot create` run.

    This object is passed by reference through the Orchestrator to each
    agent's `run()` call -- agents read what they need from it and the
    Orchestrator (not the agents) decides what gets written back, so
    there's a single place where state mutation happens.
    """

    goal: str
    project_name: str = ""
    tasks: list[str] = field(default_factory=list)
    architecture: dict = field(default_factory=dict)
    files: list[GeneratedFile] = field(default_factory=list)
    completed_steps: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def mark_step_complete(self, step_name: str) -> None:
        self.completed_steps.append(step_name)

    def record_error(self, message: str) -> None:
        self.errors.append(message)

    def add_file(self, generated_file: GeneratedFile) -> None:
        self.files.append(generated_file)

    def get_file_content(self, relative_path: str) -> Optional[str]:
        for f in self.files:
            if f.path == relative_path:
                return f.content
        return None

    def to_dict(self) -> dict:
        return asdict(self)

    def save(self, logs_dir: Path) -> Path:
        """Dump memory to `logs/<project_name>-<timestamp>.json` for
        auditability and later `explain`/`improve` lookups."""
        logs_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        out_path = logs_dir / f"{self.project_name or 'project'}-{stamp}.json"
        out_path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
        return out_path
