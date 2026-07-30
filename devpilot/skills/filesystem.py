"""
skills/filesystem.py
====================
Complete Filesystem Skill for physical file and directory operations in DevPilot.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from core.event_bus import EventBus


class FilesystemSkill:
    """Skill exposing robust physical filesystem CRUD operations."""

    def __init__(self, root_dir: str | Path = ".", bus: Optional['EventBus'] = None) -> None:
        self.root_dir = Path(root_dir).resolve()
        self._bus = bus

    def _safe_relative(self, p: Path) -> str:
        try:
            return str(p.relative_to(self.root_dir))
        except ValueError:
            return str(p)

    def resolve_path(self, path: str | Path) -> Path:
        p = Path(path)
        if not p.is_absolute():
            p = (self.root_dir / p).resolve()
        return p

    def read_file(self, path: str | Path) -> str:
        p = self.resolve_path(path)
        if self._bus:
            self._bus.publish("FileReading", file_path=self._safe_relative(p))
        return p.read_text(encoding="utf-8", errors="replace")

    def read_directory(self, path: str | Path = ".") -> List[str]:
        p = self.resolve_path(path)
        return [self._safe_relative(f) for f in p.iterdir()]

    def write_file(self, path: str | Path, content: str) -> Path:
        p = self.resolve_path(path)
        if self._bus:
            is_new = not p.exists()
            event_name = "FileCreating" if is_new else "FileEditing"
            self._bus.publish(event_name, file_path=self._safe_relative(p))
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return p

    def overwrite_file(self, path: str | Path, content: str) -> Path:
        return self.write_file(path, content)

    def append_file(self, path: str | Path, content: str) -> Path:
        p = self.resolve_path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a", encoding="utf-8") as f:
            f.write(content)
        return p

    def replace_text(self, path: str | Path, old: str, new: str) -> bool:
        p = self.resolve_path(path)
        if not p.exists():
            return False
        content = p.read_text(encoding="utf-8", errors="replace")
        if old not in content:
            return False
        new_content = content.replace(old, new)
        p.write_text(new_content, encoding="utf-8")
        return True

    def rename_file(self, old_path: str | Path, new_path: str | Path) -> Path:
        src = self.resolve_path(old_path)
        dst = self.resolve_path(new_path)
        if self._bus:
            self._bus.publish("FileEditing", file_path=self._safe_relative(dst), old_path=self._safe_relative(src))
        dst.parent.mkdir(parents=True, exist_ok=True)
        return src.rename(dst)

    def delete_file(self, path: str | Path) -> bool:
        p = self.resolve_path(path)
        if p.is_file():
            if self._bus:
                self._bus.publish("FileDeleting", file_path=self._safe_relative(p))
            p.unlink()
            return True
        return False

    def move_file(self, src: str | Path, dst: str | Path) -> Path:
        return self.rename_file(src, dst)

    def copy_file(self, src: str | Path, dst: str | Path) -> Path:
        s = self.resolve_path(src)
        d = self.resolve_path(dst)
        d.parent.mkdir(parents=True, exist_ok=True)
        return Path(shutil.copy2(s, d))

    def create_directory(self, path: str | Path) -> Path:
        p = self.resolve_path(path)
        p.mkdir(parents=True, exist_ok=True)
        return p

    def delete_directory(self, path: str | Path) -> bool:
        p = self.resolve_path(path)
        if p.is_dir():
            shutil.rmtree(p)
            return True
        return False

    def exists(self, path: str | Path) -> bool:
        return self.resolve_path(path).exists()

    def list_directory(self, path: str | Path = ".") -> List[str]:
        return self.read_directory(path)

    def glob(self, pattern: str) -> List[str]:
        return [self._safe_relative(p) for p in self.root_dir.glob(pattern)]
