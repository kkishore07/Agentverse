"""
tui/widgets/sidebar.py
========================
Left-hand sidebar: a `Tree` of the current workspace's files and a small
`DataTable` of session stats. Both are real interactive widgets (the Tree
supports expand/collapse and selection) rather than a block of printed
text, per the brief's "prioritize interactivity" direction.
"""

from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import DataTable, Label, Tree


class Sidebar(Vertical):
    DEFAULT_CSS = """
    Sidebar {
        width: 34;
        border-right: solid $primary-darken-2;
        padding: 1;
    }
    Sidebar > Label {
        color: $foreground 50%;
        text-style: bold;
        margin-top: 1;
    }
    Sidebar > Label:first-child {
        margin-top: 0;
    }
    Sidebar Tree {
        height: 10;
    }
    Sidebar DataTable {
        height: auto;
    }
    """

    def compose(self) -> ComposeResult:
        yield Label("📁 WORKSPACE")
        yield Tree("root", id="workspace-tree")
        yield Label("📊 SESSION")
        table = DataTable(id="session-table", show_header=False, cursor_type="none")
        table.add_columns("key", "value")
        yield table

    def populate_workspace(self, root_dir: Path, workspace_info: dict) -> None:
        tree = self.query_one("#workspace-tree", Tree)
        tree.root.label = f"📦 {workspace_info.get('project_name', root_dir.name)}"
        tree.root.expand()
        _build_tree(tree.root, root_dir, depth=0)

    def update_session(self, *, model_name: str, language: str, file_count: int, git: bool, messages: int) -> None:
        table = self.query_one("#session-table", DataTable)
        table.clear()
        table.add_row("Model", model_name)
        table.add_row("Language", language)
        table.add_row("Files", str(file_count))
        table.add_row("Git", "yes" if git else "no")
        table.add_row("Messages", str(messages))


def _build_tree(node, path: Path, depth: int, max_depth: int = 2, max_entries: int = 40) -> None:
    if depth >= max_depth:
        return
    try:
        entries = sorted(
            [p for p in path.iterdir() if not p.name.startswith(".") and p.name != "__pycache__"],
            key=lambda p: (p.is_file(), p.name.lower()),
        )
    except OSError:
        return

    for entry in entries[:max_entries]:
        if entry.is_dir():
            child = node.add(f"📂 {entry.name}")
            _build_tree(child, entry, depth + 1, max_depth, max_entries)
        else:
            node.add_leaf(f"📄 {entry.name}")
