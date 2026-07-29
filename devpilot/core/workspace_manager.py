"""
core/workspace_manager.py
=========================
WorkspaceManager: Coordinates physical file operations and event bus notifications.
Pipeline: Generated Artifacts -> WorkspaceManager -> FilesystemSkill -> Physical Disk Write -> Verification -> Emit Events -> Refresh UI.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Optional

from core.event_bus import (
    EVENT_FILE_CONFIRMED,
    EVENT_FILE_CREATING,
    EVENT_FILE_EDITING,
    EventBus,
)
from skills.filesystem import FilesystemSkill

EVENT_FILE_CREATED = "file_created"
EVENT_FILE_UPDATED = "file_updated"
EVENT_FILE_DELETED = "file_deleted"
EVENT_FILE_RENAMED = "file_renamed"


@dataclass
class FileArtifact:
    path: str
    content: str = ""
    action: str = "create"  # create, update, rename, delete
    old_path: Optional[str] = None


class WorkspaceManager:
    """Active coding agent manager for verified physical disk modifications & event dispatching."""

    def __init__(self, workspace_dir: str | Path = ".", bus: Optional[EventBus] = None) -> None:
        self.workspace_dir = Path(workspace_dir).resolve()
        self.bus = bus
        self.fs = FilesystemSkill(self.workspace_dir, bus=self.bus)

    def _emit(self, event_type: str, **kwargs: Any) -> None:
        if self.bus:
            self.bus.publish(event_type, **kwargs)

    def verify_write(self, target_path: Path) -> bool:
        """Verify that the target file physically exists on disk and is a valid file."""
        try:
            return target_path.exists() and target_path.is_file()
        except Exception:
            return False

    def apply_artifact(self, artifact: FileArtifact) -> Path | None:
        action = artifact.action.lower()
        if action in ("create", "write"):
            return self.create_file(artifact.path, artifact.content)
        elif action in ("update", "edit", "modify"):
            return self.update_file(artifact.path, artifact.content)
        elif action == "rename":
            return self.rename_file(artifact.old_path or artifact.path, artifact.path)
        elif action == "delete":
            self.delete_file(artifact.path)
            return None
        else:
            return self.create_file(artifact.path, artifact.content)

    def create_file(self, rel_path: str, content: str) -> Path:
        self._emit(EVENT_FILE_CREATING, path=rel_path, content=content)
        target = self.fs.write_file(rel_path, content)
        if not self.verify_write(target):
            raise IOError(f"Filesystem write failed: {target} does not exist on disk after write.")
        self._emit(EVENT_FILE_CONFIRMED, path=rel_path)
        self._emit(EVENT_FILE_CREATED, path=rel_path)
        return target

    def update_file(self, rel_path: str, content: str) -> Path:
        self._emit(EVENT_FILE_EDITING, path=rel_path, content=content)
        target = self.fs.overwrite_file(rel_path, content)
        if not self.verify_write(target):
            raise IOError(f"Filesystem update failed: {target} does not exist on disk after update.")
        self._emit(EVENT_FILE_CONFIRMED, path=rel_path)
        self._emit(EVENT_FILE_UPDATED, path=rel_path)
        return target

    def rename_file(self, old_path: str, new_path: str) -> Path:
        target = self.fs.rename_file(old_path, new_path)
        if not self.verify_write(target):
            raise IOError(f"Filesystem rename failed: {target} does not exist on disk after rename.")
        self._emit(EVENT_FILE_RENAMED, old_path=old_path, new_path=new_path)
        return target

    def delete_file(self, rel_path: str) -> bool:
        target = self.fs.resolve_path(rel_path)
        success = self.fs.delete_file(rel_path)
        if success and not target.exists():
            self._emit(EVENT_FILE_DELETED, path=rel_path)
            return True
        return False
