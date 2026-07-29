"""
agents/writer.py
=================
The Project Writer. Unlike the other agents, it never calls the LLM --
its only job is to take everything the pipeline has generated and
materialize it as real folders/files on disk, safely.

Kept as a distinct component (not folded into the Orchestrator) so the
"write to disk" concern -- and its safety guarantees (`safe_join`) --
stays isolated and independently testable.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from core.memory import GeneratedFile, ProjectMemory
from utils.fs import write_text_file


@dataclass(frozen=True)
class WriteResult:
    project_root: Path
    written_paths: list[Path]


class ProjectWriter:
    """Writes a `ProjectMemory`'s accumulated files to the workspace."""

    def __init__(self, workspace_dir: Path) -> None:
        self._workspace_dir = workspace_dir

    def write(self, memory: ProjectMemory, project_slug: str) -> WriteResult:
        """Create `workspace/<project_slug>/` and write every file recorded
        in `memory.files`.

        Args:
            memory: The accumulated project state (must have `.files` populated).
            project_slug: Filesystem-safe directory name for this project.

        Returns:
            WriteResult with the project root and every path written.
        """
        project_root = self._workspace_dir / project_slug
        project_root.mkdir(parents=True, exist_ok=True)

        written: list[Path] = []
        for f in memory.files:
            path = write_text_file(project_root, f.path, f.content)
            written.append(path)

        return WriteResult(project_root=project_root, written_paths=written)

    @staticmethod
    def record(memory: ProjectMemory, path: str, content: str, purpose: str = "") -> None:
        """Helper for the Orchestrator to append a generated file to memory
        in one call, keeping `GeneratedFile` construction in one place."""
        memory.add_file(GeneratedFile(path=path, purpose=purpose, content=content))
