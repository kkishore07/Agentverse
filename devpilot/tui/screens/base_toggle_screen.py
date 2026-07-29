"""
tui/screens/base_toggle_screen.py
===================================
Generic base class for AgentsScreen and SkillsScreen. Eliminates ~60 lines
of duplicated toggle / refresh / navigation logic.

Subclasses override:
  _title()      → str   header text
  _icon()       → str   icon emoji for the panel
  _get_items()  → dict[str, str]  {name: description}
  _is_enabled() → bool
  _enable(name)
  _disable(name)
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Footer, OptionList, Static
from textual.widgets.option_list import Option


class ToggleListScreen(ModalScreen[None]):
    """Premium base for list-of-toggles modal screens."""

    BINDINGS = [
        Binding("escape", "dismiss_screen", "Close"),
        Binding("space",  "toggle_selected", "Toggle", show=True),
        Binding("enter",  "toggle_selected", "Toggle", show=False),
    ]

    DEFAULT_CSS = """
    ToggleListScreen {
        align: center middle;
        background: $background 60%;
    }

    ToggleListScreen > Container {
        width: 72;
        max-height: 34;
        border: tall $primary;
        background: $surface;
        padding: 2 3;
    }

    ToggleListScreen .tl-title {
        text-style: bold;
        color: $primary;
        height: 2;
        margin-bottom: 1;
        padding-bottom: 1;
        border-bottom: solid $panel;
    }

    ToggleListScreen .tl-subtitle {
        color: $foreground 50%;
        height: 1;
        margin-bottom: 1;
    }

    ToggleListScreen OptionList {
        height: auto;
        max-height: 20;
        border: none;
        background: transparent;
        padding: 0;
    }

    ToggleListScreen OptionList > .option-list--option {
        padding: 1 2;
        height: 3;
    }

    ToggleListScreen OptionList > .option-list--option-highlighted {
        background: $boost;
        border-left: thick $primary;
        padding-left: 1;
    }

    ToggleListScreen .tl-hint {
        color: $foreground 50%;
        height: 1;
        margin-top: 1;
        border-top: solid $panel;
        padding-top: 1;
    }
    """

    # ---- Subclass overrides (required) -----------------------------------

    def _title(self) -> str:
        return "Select"

    def _icon(self) -> str:
        return "⚙"

    def _subtitle(self) -> str:
        return ""

    def _get_items(self) -> dict[str, str]:
        return {}

    def _is_enabled(self, name: str) -> bool:
        return False

    def _enable(self, name: str) -> None:
        pass

    def _disable(self, name: str) -> None:
        pass

    # ---- Compose ---------------------------------------------------------

    def compose(self) -> ComposeResult:
        with Container():
            yield Static(
                f"{self._icon()}  {self._title()}",
                classes="tl-title",
            )
            if self._subtitle():
                yield Static(self._subtitle(), classes="tl-subtitle")
            yield OptionList(id="tl-list")
            yield Static(
                "↑ ↓ navigate  ·  Space / Enter toggle  ·  Esc close",
                classes="tl-hint",
            )
        yield Footer()

    def on_mount(self) -> None:
        self._refresh_list()

    def _refresh_list(self) -> None:
        option_list = self.query_one("#tl-list", OptionList)
        option_list.clear_options()
        for name, description in self._get_items().items():
            enabled = self._is_enabled(name)
            if enabled:
                badge = "[green]● on [/green]"
            else:
                badge = "[dim]○ off[/dim]"
            option_list.add_option(
                Option(f"{badge}  [b]{name}[/b]  [dim]—[/dim]  {description}", id=name)
            )
        option_list.focus()

    # ---- Actions ---------------------------------------------------------

    def action_toggle_selected(self) -> None:
        option_list = self.query_one("#tl-list", OptionList)
        if option_list.highlighted is None:
            return
        option = option_list.get_option_at_index(option_list.highlighted)
        self._toggle(option.id)

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        self._toggle(event.option.id)

    def _toggle(self, name: str) -> None:
        if self._is_enabled(name):
            self._disable(name)
            self.app.notify(f"{name} disabled", title=self._title(), timeout=2)
        else:
            self._enable(name)
            self.app.notify(f"{name} enabled", title=self._title(), severity="information", timeout=2)
        self._refresh_list()

    def action_dismiss_screen(self) -> None:
        self.dismiss(None)
