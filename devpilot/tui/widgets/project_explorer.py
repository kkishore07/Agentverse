"""
tui/widgets/project_explorer.py
================================
Left panel dedicated strictly to the workspace directory tree and project exploration.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import ClassVar

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.message import Message
from textual.widgets import Button, DirectoryTree, Input, Label, Static
from textual.widgets._directory_tree import DirEntry


from rich.text import Text


class FileSelectedForPreview(Message):
    """Event posted when a user selects a file for preview."""
    def __init__(self, file_path: str) -> None:
        self.file_path = file_path
        super().__init__()


import subprocess

class WorkspaceDirectoryTree(DirectoryTree):
    """Customized DirectoryTree with file counts and clean icon formatting."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._git_status = self._get_git_status()

    def _get_git_status(self) -> dict[str, str]:
        status_map = {}
        try:
            # We assume root path is self.path or .
            output = subprocess.check_output(["git", "status", "--porcelain"], text=True, stderr=subprocess.DEVNULL)
            for line in output.splitlines():
                if len(line) > 3:
                    state = line[:2]
                    file_path = line[3:].strip()
                    file_name = Path(file_path).name
                    if "M" in state:
                        status_map[file_name] = "[#F59E0B][M][/]"
                    elif "A" in state or "??" in state:
                        status_map[file_name] = "[#10B981][A][/]" if "A" in state else "[#A5A5A5][U][/]"
                    elif "D" in state:
                        status_map[file_name] = "[#EF4444][D][/]"
        except Exception:
            pass
        return status_map

    def render_label(self, node, base_style, node_style) -> Text:
        node_label = node.label.plain
        path = node.data.path if node.data else None
        
        if path and path.is_dir():
            icon = "📂" if node.is_expanded else "📁"
            return Text.from_markup(f"{icon} [bold #ECECEC]{node_label}[/]")
        else:
            icon = "📄"
            if node_label.endswith(".py"): icon = "🐍"
            elif node_label.endswith((".js", ".jsx", ".ts", ".tsx")): icon = "🟨"
            elif node_label.endswith((".md", ".txt")): icon = "📝"
            elif node_label.endswith(".json"): icon = "🔧"

            status = self._git_status.get(node_label, "")
            
            size_str = ""
            if path and path.exists():
                try:
                    size_bytes = path.stat().st_size
                    if size_bytes < 1024:
                        size_str = f" [dim]{size_bytes}B[/]"
                    elif size_bytes < 1024 * 1024:
                        size_str = f" [dim]{size_bytes // 1024}KB[/]"
                    else:
                        size_str = f" [dim]{size_bytes // (1024 * 1024)}MB[/]"
                except Exception:
                    pass

            return Text.from_markup(f"{icon} [#ECECEC]{node_label}[/]{size_str} {status}")

class ProjectExplorer(Container):
    """Left Panel container housing strictly project files, directory tree, search, and stats."""

    DEFAULT_CSS = """
    ProjectExplorer {
        width: 30;
        min-width: 20;
        max-width: 60;
        height: 100%;
        background: #111111;
        border-right: solid #2C2C2C;
        padding: 0 1;
    }

    #pe-header {
        height: 3;
        padding-top: 1;
        border-bottom: solid #2C2C2C;
    }

    .pe-title {
        text-style: bold;
        color: #3B82F6;
        width: 1fr;
    }

    .pe-stats {
        color: #A5A5A5;
        text-align: right;
    }

    #pe-search {
        margin: 1 0;
        background: #1F1F1F;
        border: none;
        height: 1;
        padding: 0 1;
        color: #ECECEC;
    }

    #pe-controls {
        height: 1;
        margin-bottom: 1;
    }

    .pe-btn {
        width: 1fr;
        height: 1;
        border: none;
        background: #1F1F1F;
        color: #A5A5A5;
        min-width: 8;
    }
    .pe-btn:hover {
        background: #3B82F6;
        color: #FFFFFF;
    }

    #pe-tree {
        height: 1fr;
        background: #111111;
        color: #ECECEC;
        overflow-x: auto;
    }
    """

    def __init__(self, root_path: str = ".", name: str | None = None, id: str | None = "project-explorer", classes: str | None = None, disabled: bool = False) -> None:
        super().__init__(name=name, id=id, classes=classes, disabled=disabled)
        self.root_path = root_path
        self._file_count = 0
        self._dir_count = 0
        self._calc_stats()

    def _calc_stats(self) -> None:
        try:
            for _, dirs, files in os.walk(self.root_path):
                # Ignore hidden dirs
                dirs[:] = [d for d in dirs if not d.startswith(".")]
                self._dir_count += len(dirs)
                self._file_count += len(files)
                if self._file_count > 500:  # Cap scan
                    break
        except Exception:
            pass

    def compose(self) -> ComposeResult:
        with Horizontal(id="pe-header"):
            yield Label("📂 Workspace", classes="pe-title")
            yield Label(f"{self._file_count} files", classes="pe-stats")

        yield Input(placeholder="Search files...", id="pe-search")

        with Horizontal(id="pe-controls"):
            yield Button("Expand All", id="pe-expand", classes="pe-btn")
            yield Button("Collapse", id="pe-collapse", classes="pe-btn")

        yield WorkspaceDirectoryTree(self.root_path, id="pe-tree")

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        event.stop()
        self.post_message(FileSelectedForPreview(str(event.path)))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        tree = self.query_one("#pe-tree", WorkspaceDirectoryTree)
        if event.button.id == "pe-expand":
            tree.root.expand_all()
        elif event.button.id == "pe-collapse":
            tree.root.collapse_all()
