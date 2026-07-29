"""
tui/screens/help_screen.py
============================
Keyboard reference & command cheatsheet (Ctrl+H or /help).
Two-panel layout: shortcuts table on the left, commands table on the right.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import DataTable, Footer, Static


SHORTCUTS = [
    ("Ctrl+P",     "Command palette"),
    ("Ctrl+A",     "Browse agents"),
    ("Ctrl+M",     "Switch model"),
    ("Ctrl+S",     "Settings"),
    ("Ctrl+T",     "Theme picker"),
    ("Ctrl+H",     "This help screen"),
    ("Ctrl+L",     "Clear conversation"),
    ("Ctrl+/",     "Help"),
    ("/",          "Slash command menu"),
    ("↑ ↓",        "Navigate lists"),
    ("Enter",      "Select / send"),
    ("Esc",        "Close popup"),
    ("Ctrl+C/Q",   "Quit DevPilot"),
]

COMMANDS = [
    ("/agents",    "Browse and toggle agents"),
    ("/models",    "Switch active LLM model"),
    ("/skills",    "Browse and toggle skills"),
    ("/settings",  "Edit settings"),
    ("/theme",     "Open theme picker"),
    ("/history",   "Show conversation history"),
    ("/status",    "System health check"),
    ("/project",   "Show workspace info"),
    ("/clear",     "Clear the conversation"),
    ("/exit",      "Quit DevPilot"),
]


class HelpScreen(ModalScreen[None]):
    """Keyboard shortcuts and slash command reference."""

    BINDINGS = [Binding("escape", "dismiss_screen", "Close")]

    DEFAULT_CSS = """
    HelpScreen {
        align: center middle;
        background: $background 60%;
    }

    HelpScreen > Container {
        width: 90;
        max-height: 34;
        border: tall $primary;
        background: $surface;
        padding: 2 3;
    }

    HelpScreen .h-title {
        text-style: bold;
        color: $primary;
        height: 2;
        margin-bottom: 1;
        padding-bottom: 1;
        border-bottom: solid $panel;
    }

    HelpScreen .h-section {
        color: $foreground 50%;
        text-style: bold;
        height: 1;
        margin-bottom: 1;
    }

    HelpScreen DataTable {
        height: auto;
        max-height: 18;
        background: transparent;
        border: none;
        margin-bottom: 1;
    }

    HelpScreen .h-col {
        width: 1fr;
        padding-right: 2;
    }

    HelpScreen .h-hint {
        color: $foreground 50%;
        height: 1;
        margin-top: 1;
        border-top: solid $panel;
        padding-top: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Container():
            yield Static("⌨  Help & Reference", classes="h-title")
            with Horizontal():
                with Vertical(classes="h-col"):
                    yield Static("KEYBOARD SHORTCUTS", classes="h-section")
                    yield DataTable(id="shortcuts-table", cursor_type="none", show_header=False)
                with Vertical(classes="h-col"):
                    yield Static("SLASH COMMANDS", classes="h-section")
                    yield DataTable(id="commands-table", cursor_type="none", show_header=False)
            yield Static("Esc to close", classes="h-hint")
        yield Footer()

    def on_mount(self) -> None:
        shortcuts = self.query_one("#shortcuts-table", DataTable)
        shortcuts.add_columns("Key", "Action")
        for key, action in SHORTCUTS:
            shortcuts.add_row(f"[bold]{key}[/bold]", action)

        commands = self.query_one("#commands-table", DataTable)
        commands.add_columns("Cmd", "Description")
        for cmd, desc in COMMANDS:
            commands.add_row(f"[bold]{cmd}[/bold]", desc)

    def action_dismiss_screen(self) -> None:
        self.dismiss(None)
