"""
core/context.py
===============
Manages the ProjectContext, the shared state passed between agents
during a pipeline execution. Agents communicate only through this context.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ProjectContext:
    """Shared state passed between agents in a pipeline."""
    
    # Core identifying info
    goal: str
    workspace_dir: Path
    
    # State populated during pipeline
    project_name: str = ""
    tasks: list[str] = field(default_factory=list)
    tech_stack: list[str] = field(default_factory=list)
    
    # File specifications planned by the architect
    planned_files: list[dict[str, str]] = field(default_factory=list)
    
    # Files generated or modified by Coder/Fixer
    written_files: list[str] = field(default_factory=list)
    
    # Validation and Test states
    validation_passed: bool = False
    validation_errors: list[str] = field(default_factory=list)
    tests_passed: bool = False
    test_reports: list[str] = field(default_factory=list)
    
    # General metadata store for unstructured agent communication
    metadata: dict[str, Any] = field(default_factory=dict)
    
    # History of agent execution steps
    execution_history: list[str] = field(default_factory=list)

    def log_execution(self, agent_name: str, status: str) -> None:
        """Log an agent's execution phase into the context."""
        self.execution_history.append(f"[{agent_name}] {status}")
