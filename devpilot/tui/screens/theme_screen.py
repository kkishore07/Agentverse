"""
tui/screens/theme_screen.py
============================
Dedicated live theme picker with instant preview and robust ListView rendering.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.screen import ModalScreen
from textual.widgets import Footer, ListItem, ListView, Static

from tui.themes import THEMES, THEME_ACCENTS, display_name_for, theme_id


class ThemeScreen(ModalScreen[str | None]):
    """Live theme picker with instant preview using robust ListView."""

    BINDINGS = [
        Binding("escape", "revert_theme", "Revert & Close"),
        Binding("enter",  "confirm_theme", "Apply"),
    ]

    DEFAULT_CSS = """
    ThemeScreen {
        align: center middle;
        background: #090909 80%;
    }

    ThemeScreen > Container {
        width: 65%;
        height: 65%;
        min-width: 50;
        max-width: 80;
        border: solid #3B82F6;
        background: #111111;
        padding: 1 2;
    }

    ThemeScreen .th-title {
        text-style: bold;
        color: #3B82F6;
        height: 2;
        margin-bottom: 1;
        border-bottom: solid #2C2C2C;
    }

    ThemeScreen ListView {
        height: 1fr;
        border: solid #2C2C2C;
        background: #171717;
        padding: 1;
    }

    ThemeScreen ListItem {
        height: 3;
        padding: 0 1;
        color: #ECECEC;
    }

    ThemeScreen ListItem:hover {
        background: #1F1F1F;
    }

    ThemeScreen ListItem.-highlighted {
        background: #1F1F1F;
        border-left: thick #3B82F6;
    }

    ThemeScreen .th-hint {
        color: #A5A5A5;
        height: 1;
        margin-top: 1;
        border-top: solid #2C2C2C;
        padding-top: 1;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._original_theme: str = ""

    def compose(self) -> ComposeResult:
        with Container():
            yield Static("🎨 Live Theme Switcher", classes="th-title")
            yield ListView(id="th-list")
            yield Static(
                "↑ ↓ live preview  ·  Enter apply  ·  Esc revert",
                classes="th-hint",
            )
        yield Footer()

    def on_mount(self) -> None:
        self._original_theme = self.app.theme
        self._rebuild_list()

    def _rebuild_list(self) -> None:
        list_view = self.query_one("#th-list", ListView)
        list_view.clear()
        current_id = self.app.theme

        for display_name, tid in THEMES.items():
            is_current = tid == current_id
            accent = THEME_ACCENTS.get(display_name, "#3B82F6")
            swatch = f"[{accent}]*[/]"
            label = f"[bold #ECECEC]{display_name}[/]" if is_current else f"[#ECECEC]{display_name}[/]"
            active_badge = "  [bold #10B981](Active)[/]" if is_current else ""
            
            item = ListItem(
                Static(f"{swatch}  {label}{active_badge}"),
                name=tid,
                id=f"th-{tid.replace('-', '_')}",
            )
            list_view.append(item)

        list_view.focus()

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        """Live preview: apply theme instantly on navigation."""
        if event.item and hasattr(event.item, "name") and event.item.name:
            self.app.theme = event.item.name

    def action_confirm_theme(self) -> None:
        self.dismiss(self.app.theme)

    def action_revert_theme(self) -> None:
        self.app.theme = self._original_theme
        self.dismiss(None)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.item and hasattr(event.item, "name") and event.item.name:
            self.app.theme = event.item.name
        self.dismiss(self.app.theme)
