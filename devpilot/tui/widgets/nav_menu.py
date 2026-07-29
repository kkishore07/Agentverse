# -*- coding: utf-8 -*-
"""
tui/widgets/nav_menu.py
========================
Left-sidebar navigation menu. The primary way users switch between sections
(Chat, Agents, Models, Skills, Plugins, Workspace, History, Settings, Logs, Help).

Design goals:
  - Arrow key + mouse selection
  - Highlights current section with accent border-left
  - Sends NavMenu.Selected message when section changes
  - Keyboard shortcut badges shown for common sections
  - Section dividers between logical groups
  - Premium feel: generous padding, muted icons, bold selected state
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class NavItem:
    id: str
    label: str
    icon: str
    shortcut: str = ""
    divider_above: bool = False   # renders a thin separator before this item


NAV_ITEMS: list[NavItem] = [
    NavItem("chat",      "Chat",       ">",  ""),
    NavItem("agents",    "Agents",     "@",  "^A", divider_above=False),
    NavItem("models",    "Models",     "#",  "^M"),
    NavItem("skills",    "Skills",     "*",  "^S"),
    NavItem("plugins",   "Plugins",    "+",  ""),
    NavItem("workspace", "Workspace",  "~",  "", divider_above=True),
    NavItem("history",   "History",    ":",  "^H"),
    NavItem("settings",  "Settings",   "=",  ""),
    NavItem("logs",      "Logs",       "|",  ""),
    NavItem("help",      "Help",       "?",  "^/", divider_above=True),
]

# Fallback icons if Nerd Fonts not available
_ASCII_ICONS: dict[str, str] = {
    "chat":      "▶",
    "agents":    "⚙",
    "models":    "◈",
    "skills":    "✦",
    "plugins":   "⊞",
    "workspace": "⌂",
    "history":   "⏷",
    "settings":  "≡",
    "logs":      "≈",
    "help":      "?",
}


# ---------------------------------------------------------------------------
# NavMenu widget
# ---------------------------------------------------------------------------

class NavMenu(Widget):
    """Interactive sidebar navigation with arrow/mouse selection."""

    COMPONENT_CLASSES: ClassVar[set[str]] = {
        "nav-menu--item",
        "nav-menu--item-selected",
        "nav-menu--divider",
        "nav-menu--shortcut",
        "nav-menu--header",
    }

    DEFAULT_CSS = """
    NavMenu {
        width: 15%;
        min-width: 18;
        max-width: 25;
        height: 1fr;
        background: $surface;
        border-right: solid $panel;
        padding: 1 0;
        overflow-y: auto;
        overflow-x: hidden;
    }

    NavMenu .nav-header {
        color: $foreground 50%;
        text-style: bold;
        padding: 1 2 0 2;
        height: 2;
        text-align: left;
    }

    NavMenu .nav-divider {
        height: 1;
        color: $panel;
        padding: 0 2;
    }

    NavMenu .nav-item {
        height: 3;
        padding: 0 2;
        color: $foreground 50%;
        layout: horizontal;
        align: left middle;
    }

    NavMenu .nav-item:hover {
        background: $boost;
        color: $foreground;
    }

    NavMenu .nav-item.-selected {
        background: $boost;
        color: $primary;
        border-left: thick $primary;
        padding-left: 1;
    }

    NavMenu .nav-item .item-icon {
        width: 3;
        text-style: bold;
    }

    NavMenu .nav-item .item-label {
        width: 1fr;
    }

    NavMenu .nav-item.-selected .item-label {
        text-style: bold;
        color: $primary;
    }

    NavMenu .nav-item .item-shortcut {
        width: 4;
        color: $foreground 50%;
        text-align: right;
    }

    NavMenu .nav-item.-selected .item-shortcut {
        color: $primary;
    }
    """

    BINDINGS = [
        Binding("up",    "cursor_up",   "Up",   show=False),
        Binding("down",  "cursor_down", "Down", show=False),
        Binding("enter", "select",      "Select", show=False),
        Binding("k",     "cursor_up",   "Up",   show=False),
        Binding("j",     "cursor_down", "Down", show=False),
    ]

    # ---- Messages -----------------------------------------------------------

    class Selected(Message):
        """Posted when the active nav section changes."""
        def __init__(self, item_id: str) -> None:
            self.item_id = item_id
            super().__init__()

    # ---- Reactive -----------------------------------------------------------

    current: reactive[str] = reactive("chat", init=False)
    _cursor_idx: reactive[int] = reactive(0, init=False)

    # ---- Compose ------------------------------------------------------------

    def compose(self) -> ComposeResult:
        yield Static("DEVPILOT", classes="nav-header")
        for i, item in enumerate(NAV_ITEMS):
            if item.divider_above:
                yield Static("─" * 16, classes="nav-divider")
            yield NavItemWidget(item, selected=(i == 0), index=i)

    # ---- Keyboard -----------------------------------------------------------

    def action_cursor_up(self) -> None:
        items = self.query(NavItemWidget)
        count = len(items)
        if count == 0:
            return
        self._cursor_idx = (self._cursor_idx - 1) % count
        self._apply_cursor()

    def action_cursor_down(self) -> None:
        items = self.query(NavItemWidget)
        count = len(items)
        if count == 0:
            return
        self._cursor_idx = (self._cursor_idx + 1) % count
        self._apply_cursor()

    def action_select(self) -> None:
        items = list(self.query(NavItemWidget))
        if 0 <= self._cursor_idx < len(items):
            items[self._cursor_idx].activate()

    def _apply_cursor(self) -> None:
        items = list(self.query(NavItemWidget))
        for i, w in enumerate(items):
            w.set_selected(i == self._cursor_idx)

    # ---- Public API ---------------------------------------------------------

    def set_active(self, item_id: str) -> None:
        """Programmatically set the active section."""
        items = list(self.query(NavItemWidget))
        for i, w in enumerate(items):
            selected = w.item.id == item_id
            w.set_selected(selected)
            if selected:
                self._cursor_idx = i

    # ---- Child selection callback -------------------------------------------

    def on_nav_item_widget_activated(self, event: "NavItemWidget.Activated") -> None:
        event.stop()
        items = list(self.query(NavItemWidget))
        for i, w in enumerate(items):
            selected = w.item.id == event.item_id
            w.set_selected(selected)
            if selected:
                self._cursor_idx = i
        self.current = event.item_id
        self.post_message(NavMenu.Selected(event.item_id))

    def on_focus(self) -> None:
        self._apply_cursor()


# ---------------------------------------------------------------------------
# NavItemWidget — one row in the nav
# ---------------------------------------------------------------------------

class NavItemWidget(Static):
    """A single navigation row."""

    class Activated(Message):
        """Posted when this item is clicked or selected."""
        def __init__(self, item_id: str) -> None:
            self.item_id = item_id
            super().__init__()

    def __init__(self, item: NavItem, selected: bool = False, index: int = 0) -> None:
        self.item = item
        self._selected = selected
        self._index = index
        super().__init__(classes="nav-item" + (" -selected" if selected else ""))

    def render(self) -> str:
        icon = self.item.icon
        label = self.item.label
        shortcut = self.item.shortcut

        if shortcut:
            return f"{icon}  {label:<12}[dim]{shortcut}[/dim]"
        return f"{icon}  {label}"

    def set_selected(self, selected: bool) -> None:
        self._selected = selected
        self.set_class(selected, "-selected")

    def on_click(self) -> None:
        self.post_message(NavItemWidget.Activated(self.item.id))

    def activate(self) -> None:
        self.post_message(NavItemWidget.Activated(self.item.id))
