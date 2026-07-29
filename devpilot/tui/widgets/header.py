"""
tui/widgets/header.py
======================
DevPilotHeader — replaces Textual's generic Header widget.

Shows (left to right):
  ● Logo pill        [  DevPilot  ]
  ● Workspace name   workspace/project
  ● Git branch       ⎇ main
  ● Model name       ◈ qwen2.5-coder
  ● Connection dot   ● Connected  /  ● Offline
  ● Mode badge       CHAT / TASK
  ● Theme name       🎨 DevPilot

All fields are reactive — assigning to them triggers an instant redraw.
No rebuild, no full-screen invalidation.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static


class DevPilotHeader(Widget):
    """Premium header bar with logo, metadata, and live status."""

    DEFAULT_CSS = """
    DevPilotHeader {
        height: 3;
        background: $surface;
        border-bottom: solid $panel;
        layout: horizontal;
        align: left middle;
        padding: 0 2;
        dock: top;
    }

    DevPilotHeader .header-logo {
        background: $primary;
        color: $background;
        text-style: bold;
        padding: 0 2;
        margin-right: 2;
        height: 1;
    }

    DevPilotHeader .header-brand {
        color: $foreground;
        text-style: bold;
        padding: 0 1;
        margin-right: 1;
        height: 1;
    }

    DevPilotHeader .header-sep {
        color: $panel;
        margin: 0 1;
        width: 1;
    }

    DevPilotHeader .header-workspace {
        color: $foreground;
        text-style: bold;
        margin-right: 1;
    }

    DevPilotHeader .header-git {
        color: $accent;
        margin-right: 1;
    }

    DevPilotHeader .header-model {
        color: $secondary;
        margin-right: 1;
    }

    DevPilotHeader .header-conn-ok {
        color: $success;
    }

    DevPilotHeader .header-conn-err {
        color: $error;
    }

    DevPilotHeader .header-mode-chat {
        color: $primary;
        text-style: bold;
        padding: 0 1;
        background: $boost;
        margin: 0 1;
    }

    DevPilotHeader .header-mode-task {
        color: $warning;
        text-style: bold;
        padding: 0 1;
        background: $boost;
        margin: 0 1;
    }

    DevPilotHeader .header-theme {
        color: $foreground 40%;
        margin-left: 1;
    }

    DevPilotHeader .header-spacer {
        width: 1fr;
    }
    """

    # ---- Reactives -------------------------------------------------------

    workspace_name: reactive[str] = reactive("")
    git_branch: reactive[str]     = reactive("")
    model_name: reactive[str]     = reactive("")
    connected: reactive[bool]     = reactive(True)
    mode: reactive[str]           = reactive("CHAT")
    theme_name: reactive[str]     = reactive("")

    # ---- Compose ---------------------------------------------------------

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Static(" ◈ DevPilot ", classes="header-logo", id="hdr-logo")
            yield Static("│", classes="header-sep")
            yield Static("", classes="header-workspace", id="hdr-workspace")
            yield Static("", classes="header-git",       id="hdr-git")
            yield Static("", classes="header-spacer")
            yield Static("", classes="header-model",     id="hdr-model")
            yield Static("│", classes="header-sep")
            yield Static("", id="hdr-conn")
            yield Static("", id="hdr-mode",    classes="header-mode-chat")
            yield Static("", classes="header-theme",     id="hdr-theme")

    # ---- Watchers --------------------------------------------------------

    def watch_workspace_name(self, value: str) -> None:
        if w := self.query_one("#hdr-workspace", Static):
            w.update(f"⌂  {value}" if value else "")

    def watch_git_branch(self, value: str) -> None:
        if w := self.query_one("#hdr-git", Static):
            w.update(f"  ⎇  {value}" if value else "")

    def watch_model_name(self, value: str) -> None:
        if w := self.query_one("#hdr-model", Static):
            w.update(f"◈  {value}" if value else "")

    def watch_connected(self, value: bool) -> None:
        if w := self.query_one("#hdr-conn", Static):
            if value:
                w.update("● Connected")
                w.set_classes("header-conn-ok")
            else:
                w.update("● Offline")
                w.set_classes("header-conn-err")

    def watch_mode(self, value: str) -> None:
        if w := self.query_one("#hdr-mode", Static):
            w.update(f" {value} ")
            if value == "TASK":
                w.set_classes("header-mode-task")
            else:
                w.set_classes("header-mode-chat")

    def watch_theme_name(self, value: str) -> None:
        if w := self.query_one("#hdr-theme", Static):
            w.update(f"🎨 {value}" if value else "")
