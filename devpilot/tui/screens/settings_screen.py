"""
tui/screens/settings_screen.py
================================
Settings modal — Ctrl+S or /settings.
Premium layout with tab-like sections, real Input widgets,
inline theme picker, and save/cancel buttons.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Input, Label, OptionList, Static
from textual.widgets.option_list import Option

from tui.backend import Backend
from tui.themes import THEMES, display_name_for


class SettingsScreen(ModalScreen[None]):
    """Edit runtime settings: LLM, workspace, and theme."""

    BINDINGS = [Binding("escape", "dismiss_screen", "Close")]

    DEFAULT_CSS = """
    SettingsScreen {
        align: center middle;
        background: $background 60%;
    }

    SettingsScreen > Container {
        width: 68;
        max-height: 36;
        border: tall $primary;
        background: $surface;
        padding: 2 3;
    }

    SettingsScreen .s-title {
        text-style: bold;
        color: $primary;
        height: 2;
        margin-bottom: 1;
        padding-bottom: 1;
        border-bottom: solid $panel;
    }

    SettingsScreen .s-section {
        color: $foreground 50%;
        text-style: bold;
        height: 2;
        margin-top: 1;
        padding-top: 1;
        border-top: solid $panel;
    }

    SettingsScreen .s-row {
        height: 3;
        margin-bottom: 1;
        layout: horizontal;
        align: left middle;
    }

    SettingsScreen Label {
        width: 22;
        color: $foreground 50%;
        padding-top: 1;
    }

    SettingsScreen Input {
        width: 1fr;
        background: $boost;
    }

    SettingsScreen #theme-list {
        height: 8;
        border: none;
        background: transparent;
    }

    SettingsScreen #theme-list > .option-list--option {
        padding: 0 2;
        height: 2;
    }

    SettingsScreen #theme-list > .option-list--option-highlighted {
        background: $boost;
    }

    SettingsScreen .s-actions {
        layout: horizontal;
        align-horizontal: right;
        height: 3;
        margin-top: 1;
        border-top: solid $panel;
        padding-top: 1;
    }

    SettingsScreen Button {
        margin-left: 1;
    }
    """

    def __init__(self, backend: Backend) -> None:
        self._backend = backend
        super().__init__()

    def compose(self) -> ComposeResult:
        s = self._backend.settings
        with Container():
            yield Static("⚙  Settings", classes="s-title")

            yield Static("LLM", classes="s-section")
            with Horizontal(classes="s-row"):
                yield Label("Ollama Host")
                yield Input(value=s.ollama_host, id="host-input", placeholder="http://localhost:11434")
            with Horizontal(classes="s-row"):
                yield Label("Temperature")
                yield Input(value=str(s.llm_temperature), id="temp-input", placeholder="0.2")
            with Horizontal(classes="s-row"):
                yield Label("Max Files / Project")
                yield Input(value=str(s.max_files_per_project), id="maxfiles-input", placeholder="40")

            yield Static("Theme", classes="s-section")
            yield OptionList(id="theme-list")

            with Horizontal(classes="s-actions"):
                yield Button("Save", variant="success", id="save-btn")
                yield Button("Cancel", id="close-btn")

        yield Footer()

    def on_mount(self) -> None:
        theme_list = self.query_one("#theme-list", OptionList)
        current = display_name_for(self.app.theme)
        for name in THEMES:
            marker = "[green]●[/green]" if name == current else "[dim]○[/dim]"
            label = f"[bold]{name}[/bold]" if name == current else name
            theme_list.add_option(Option(f"{marker}  {label}", id=name))

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option_list.id == "theme-list" and event.option.id:
            from tui.themes import THEMES
            self.app.theme = THEMES[event.option.id]

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save-btn":
            self._save()
        self.dismiss(None)

    def _save(self) -> None:
        s = self._backend.settings
        host = self.query_one("#host-input", Input).value.strip()
        if host:
            s.ollama_host = host
        try:
            s.llm_temperature = float(self.query_one("#temp-input", Input).value)
        except ValueError:
            pass
        try:
            s.max_files_per_project = int(self.query_one("#maxfiles-input", Input).value)
        except ValueError:
            pass
        self._backend.rebuild_llm(s.model_name)
        self.app.notify("Settings saved", title="Settings", severity="information")

    def action_dismiss_screen(self) -> None:
        self.dismiss(None)
