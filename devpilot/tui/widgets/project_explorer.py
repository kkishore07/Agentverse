"""
tui/widgets/project_explorer.py
================================
Left panel: VS Code-style Workspace Explorer.

Features:
- File search
- Directory tree with file icons
- Git status badges (M/A/D)
- File size display
- Expand/collapse controls
- Live updates during AI generation
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
    """Customized DirectoryTree with VS Code-style icons and git status badges."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._git_status = self._get_git_status()

    def _get_git_status(self) -> dict[str, str]:
        status_map = {}
        try:
            output = subprocess.check_output(["git", "status", "--porcelain"], text=True, stderr=subprocess.DEVNULL)
            for line in output.splitlines():
                if len(line) > 3:
                    state = line[:2]
                    file_path = line[3:].strip()
                    file_name = Path(file_path).name
                    if "M" in state:
                        status_map[file_name] = "M"
                    elif "A" in state or "??" in state:
                        status_map[file_name] = "A" if "A" in state else "U"
                    elif "D" in state:
                        status_map[file_name] = "D"
        except Exception:
            pass
        return status_map

    def _get_file_icon(self, name: str, is_dir: bool, is_expanded: bool = False) -> str:
        if is_dir:
            return "▾" if is_expanded else "▸"
        # File type icons using Unicode
        lower = name.lower()
        if lower.endswith(".py"):         return "🐍"
        if lower.endswith((".js", ".mjs")): return "󰌞"  # JS fallback
        if lower.endswith((".jsx",)):     return "⚛"
        if lower.endswith((".ts", ".tsx")): return "📘"
        if lower.endswith((".md", ".rst")): return "📝"
        if lower.endswith(".json"):       return "⚙"
        if lower.endswith((".yaml", ".yml")): return "⚙"
        if lower.endswith((".html", ".htm")): return "🌐"
        if lower.endswith(".css"):        return "🎨"
        if lower.endswith((".sh", ".bash")): return "⚡"
        if lower.endswith((".env", ".cfg", ".ini", ".toml")): return "🔧"
        if lower.endswith((".png", ".jpg", ".jpeg", ".svg", ".gif")): return "🖼"
        if lower.endswith((".zip", ".tar", ".gz")): return "📦"
        if lower in ("dockerfile", "docker-compose.yml"): return "🐳"
        if lower in ("makefile", "cmakelists.txt"): return "🔨"
        if lower == "readme.md":          return "📋"
        if lower.endswith(".lock"):       return "🔒"
        return "📄"

    def render_label(self, node, base_style, node_style) -> Text:
        node_label = node.label.plain
        path = node.data.path if node.data else None

        if path and path.is_dir():
            icon = self._get_file_icon(node_label, True, node.is_expanded)
            text = Text()
            text.append(f"{icon} ", style="bold #7D8590")
            text.append(node_label, style="bold #E6EDF3")
            return text
        else:
            icon = self._get_file_icon(node_label, False)
            git_state = self._git_status.get(node_label, "")

            # Git status color
            name_style = "#E6EDF3"
            if git_state == "M":
                name_style = "#E3B341"   # amber for modified
            elif git_state == "A":
                name_style = "#56D364"   # green for added
            elif git_state == "D":
                name_style = "#F85149"   # red for deleted
            elif git_state == "U":
                name_style = "#7D8590"   # muted for untracked

            size_str = ""
            if path and path.exists():
                try:
                    size_bytes = path.stat().st_size
                    if size_bytes < 1024:
                        size_str = f" {size_bytes}B"
                    elif size_bytes < 1024 * 1024:
                        size_str = f" {size_bytes // 1024}KB"
                    else:
                        size_str = f" {size_bytes // (1024 * 1024)}MB"
                except Exception:
                    pass

            text = Text()
            text.append(f"{icon} ", style="#7D8590")
            text.append(node_label, style=name_style)
            if size_str:
                text.append(size_str, style="dim #7D8590")
            if git_state == "M":
                text.append(" M", style="bold #E3B341")
            elif git_state == "A":
                text.append(" A", style="bold #56D364")
            elif git_state == "D":
                text.append(" D", style="bold #F85149")
            return text

class ProjectExplorer(Container):
    """Left Panel: VS Code-style workspace explorer."""

    DEFAULT_CSS = """
    ProjectExplorer {
        width: 32;
        min-width: 22;
        max-width: 60;
        height: 100%;
        background: $surface;
        border-right: solid $panel;
        padding: 0;
    }

    #pe-header {
        height: 2;
        padding: 0 1;
        background: $surface;
        border-bottom: solid $panel;
        align: left middle;
    }

    .pe-title {
        text-style: bold;
        color: $foreground 60%;
        width: 1fr;
    }

    .pe-stats {
        color: $foreground 30%;
        text-align: right;
        width: auto;
    }

    #pe-search-wrap {
        height: 3;
        padding: 0 1;
        border-bottom: solid $panel;
        background: $surface;
        align: left middle;
    }

    #pe-search {
        background: $background;
        border: solid $panel;
        height: 1;
        padding: 0 1;
        color: $foreground;
        width: 1fr;
    }

    #pe-search:focus {
        border: solid $primary;
    }

    #pe-controls {
        height: 2;
        padding: 0 1;
        background: $surface;
        border-bottom: solid $panel;
        align: left middle;
    }

    .pe-btn {
        width: auto;
        height: 1;
        border: none;
        background: transparent;
        color: $foreground 40%;
        min-width: 10;
        padding: 0 1;
    }
    .pe-btn:hover {
        background: $boost;
        color: $primary;
    }

    #pe-tree {
        height: 1fr;
        background: $surface;
        color: $foreground;
        overflow-x: auto;
        padding: 0 0 0 1;
    }

    #pe-git-branch {
        height: 2;
        padding: 0 1;
        border-top: solid $panel;
        background: $surface;
        color: $accent;
        align: left middle;
    }
    """

    def __init__(self, root_path: str = ".", name: str | None = None, id: str | None = "project-explorer", classes: str | None = None, disabled: bool = False) -> None:
        super().__init__(name=name, id=id, classes=classes, disabled=disabled)
        self.root_path = root_path
        self._file_count = 0
        self._dir_count = 0
        self._calc_stats()
        self._git_branch = self._detect_branch()

    def _calc_stats(self) -> None:
        try:
            for _, dirs, files in os.walk(self.root_path):
                dirs[:] = [d for d in dirs if not d.startswith(".")]
                self._dir_count += len(dirs)
                self._file_count += len(files)
                if self._file_count > 500:
                    break
        except Exception:
            pass

    def _detect_branch(self) -> str:
        try:
            import subprocess
            out = subprocess.check_output(["git", "branch", "--show-current"], text=True, stderr=subprocess.DEVNULL)
            return out.strip() or "main"
        except Exception:
            return "main"

    def compose(self) -> ComposeResult:
        with Horizontal(id="pe-header"):
            yield Label("EXPLORER", classes="pe-title")
            yield Label(f"{self._file_count} files", classes="pe-stats")

        with Horizontal(id="pe-search-wrap"):
            yield Input(placeholder="🔍 Search files...", id="pe-search")

        with Horizontal(id="pe-controls"):
            yield Button("▾ Expand", id="pe-expand", classes="pe-btn")
            yield Button("▸ Collapse", id="pe-collapse", classes="pe-btn")

        yield WorkspaceDirectoryTree(self.root_path, id="pe-tree")

        yield Static(f"⎇  {self._git_branch}", id="pe-git-branch")

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        event.stop()
        self.post_message(FileSelectedForPreview(str(event.path)))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        tree = self.query_one("#pe-tree", WorkspaceDirectoryTree)
        if event.button.id == "pe-expand":
            tree.root.expand_all()
        elif event.button.id == "pe-collapse":
            tree.root.collapse_all()

    def reload(self) -> None:
        """Reload the directory tree (called after file writes)."""
        try:
            tree = self.query_one("#pe-tree", WorkspaceDirectoryTree)
            tree.reload()
        except Exception:
            pass
