"""
tui/widgets/status_bar.py
==========================
Premium status bar: pill-based horizontal layout with individual reactive
segments. Each segment is independently styled — mode badge gets warning
colour during TASK, connection dot goes red when Ollama is unreachable, etc.

Unlike the old single `render()` string, compose() builds real child
widgets so we can independently animate/style each pill.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static


class _Pill(Static):
    """A minimal status bar segment."""
    DEFAULT_CSS = """
    _Pill {
        height: 1;
        padding: 0 1;
        color: $foreground 50%;
    }
    """


class _Sep(Static):
    DEFAULT_CSS = """
    _Sep {
        height: 1;
        width: 1;
        color: $panel;
    }
    """
    def __init__(self) -> None:
        super().__init__("│")


class StatusBar(Widget):
    """Single-row status strip docked to the bottom."""

    DEFAULT_CSS = """
    StatusBar {
        height: 1;
        background: $surface;
        border-top: solid $panel;
        dock: bottom;
        layout: horizontal;
        align: left middle;
        padding: 0 1;
    }

    StatusBar #sb-mode {
        text-style: bold;
        background: $boost;
        padding: 0 1;
    }

    StatusBar #sb-mode.-chat {
        color: $primary;
    }

    StatusBar #sb-mode.-task {
        color: $warning;
    }

    StatusBar #sb-status {
        color: $foreground;
    }

    StatusBar #sb-agent {
        color: $secondary;
        text-style: bold;
    }

    StatusBar #sb-workspace {
        color: $foreground 50%;
    }

    StatusBar #sb-model {
        color: $accent;
    }

    StatusBar #sb-tokens {
        color: $foreground 50%;
    }

    StatusBar #sb-theme {
        color: $foreground 50%;
    }

    StatusBar #sb-hints {
        color: $panel;
        width: 1fr;
        text-align: right;
    }
    """

    mode: reactive[str]          = reactive("CHAT")
    active_agent: reactive[str]  = reactive("")
    model_name: reactive[str]    = reactive("")
    workspace_name: reactive[str] = reactive("")
    token_estimate: reactive[int] = reactive(0)
    status_text: reactive[str]   = reactive("Ready")
    theme_label: reactive[str]   = reactive("")

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Static(" CHAT ", id="sb-mode", classes="-chat")
            yield _Sep()
            yield Static("Ready",  id="sb-status",    classes="sb-pill")
            yield _Sep()
            yield Static("",       id="sb-agent",     classes="sb-pill")
            yield Static("",       id="sb-workspace",  classes="sb-pill")
            yield _Sep()
            yield Static("",       id="sb-model",     classes="sb-pill")
            yield _Sep()
            yield Static("",       id="sb-tokens",    classes="sb-pill")
            yield _Sep()
            yield Static("",       id="sb-theme",     classes="sb-pill")
            yield Static(
                "[dim]^P palette  ^A agents  ^M models  ^T themes  ^H help[/dim]",
                id="sb-hints",
            )

    # ---- Watchers --------------------------------------------------------

    def watch_mode(self, value: str) -> None:
        try:
            mode_pill = self.query_one("#sb-mode", Static)
        except Exception:
            return

        if value == "TASK":
            mode_pill.update(" TASK ")
            mode_pill.set_classes("-task")
        else:
            mode_pill.update(" CHAT ")
            mode_pill.set_classes("-chat")

    def watch_status_text(self, value: str) -> None:
        try:
            self.query_one("#sb-status", Static).update(value)
        except Exception:
            pass

    def watch_active_agent(self, value: str) -> None:
        try:
            w = self.query_one("#sb-agent", Static)
            w.update(f"⚙  {value}" if value else "")
        except Exception:
            pass

    def watch_workspace_name(self, value: str) -> None:
        try:
            w = self.query_one("#sb-workspace", Static)
            w.update(f"⌂  {value}" if value else "")
        except Exception:
            pass

    def watch_model_name(self, value: str) -> None:
        try:
            short = value.split(":")[0] if ":" in value else value
            w = self.query_one("#sb-model", Static)
            w.update(f"◈  {short}" if short else "")
        except Exception:
            pass

    def watch_token_estimate(self, value: int) -> None:
        try:
            w = self.query_one("#sb-tokens", Static)
            w.update(f"~{value:,} tok" if value else "")
        except Exception:
            pass

    def watch_theme_label(self, value: str) -> None:
        try:
            w = self.query_one("#sb-theme", Static)
            w.update(f"🎨  {value}" if value else "")
        except Exception:
            pass
