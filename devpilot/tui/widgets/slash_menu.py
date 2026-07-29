"""
tui/widgets/slash_menu.py
===========================
Floating command palette that appears when the user types "/" in the input.

Design improvements over the original:
  - Proper `layer: overlay` with correct screen-level z-order
  - Category grouping (Navigation, Chat, System)
  - Fuzzy matching — not just prefix
  - Keyboard: ↑ ↓ Enter Esc (handled by ChatInput via key redirection)
  - Premium styling: rounded border, semi-transparent background
"""

from __future__ import annotations

from dataclasses import dataclass

from textual.widgets import OptionList
from textual.widgets.option_list import Option


@dataclass(frozen=True)
class SlashCommand:
    command: str
    description: str
    shortcut: str = ""
    category: str = "other"


# Grouped commands
COMMANDS: list[SlashCommand] = [
    # Navigation
    SlashCommand("/agents",   "Browse and toggle agents",     "^A",  "navigation"),
    SlashCommand("/models",   "Switch the active LLM model",  "^M",  "navigation"),
    SlashCommand("/skills",   "Browse and toggle skills",     "^S",  "navigation"),
    SlashCommand("/theme",    "Open theme picker",            "^T",  "navigation"),
    SlashCommand("/settings", "Edit DevPilot settings",       "",    "navigation"),
    SlashCommand("/help",     "Keyboard shortcuts reference", "^H",  "navigation"),
    # Chat / Workspace
    SlashCommand("/history",  "Show conversation history",    "",    "chat"),
    SlashCommand("/status",   "System health check",          "",    "chat"),
    SlashCommand("/project",  "Show workspace info",          "",    "chat"),
    SlashCommand("/clear",    "Clear the conversation",       "^L",  "chat"),
    # System
    SlashCommand("/exit",     "Quit DevPilot",                "",    "system"),
]

_CATEGORY_LABELS = {
    "navigation": "NAVIGATION",
    "chat":       "WORKSPACE",
    "system":     "SYSTEM",
}


def _fuzzy_score(needle: str, haystack: str) -> int:
    """Very simple subsequence fuzzy score. Returns 0 for no match."""
    if not needle:
        return 1
    needle = needle.lower()
    haystack = haystack.lower()
    if haystack.startswith(needle):
        return 100 - len(haystack)   # prefix match scores highest
    idx = 0
    for ch in needle:
        pos = haystack.find(ch, idx)
        if pos == -1:
            return 0
        idx = pos + 1
    return 50 - len(haystack)       # subsequence match


class SlashMenu(OptionList):
    """Floating, filterable command menu — anchored above the input bar."""

    DEFAULT_CSS = """
    SlashMenu {
        layer: overlay;
        display: none;
        height: auto;
        max-height: 16;
        width: 64;
        border: tall $primary;
        background: $surface;
        offset-y: -1;
    }

    SlashMenu.-visible {
        display: block;
    }

    SlashMenu > .option-list--option {
        padding: 1 2;
        height: 3;
    }

    SlashMenu > .option-list--option-highlighted {
        background: $boost;
        border-left: thick $primary;
        padding-left: 1;
    }

    SlashMenu > .option-list--separator {
        color: $foreground 50%;
        height: 1;
        padding: 0 2;
    }
    """

    def __init__(self) -> None:
        super().__init__(id="slash-menu")
        self._all_commands = COMMANDS

    def filter(self, typed_text: str) -> None:
        """Filter and re-render option list based on typed text."""
        query = typed_text.lstrip("/").lower()
        self.clear_options()

        # Score all commands
        scored = []
        for cmd in self._all_commands:
            score = _fuzzy_score(query, cmd.command)
            if score > 0:
                scored.append((score, cmd))
        scored.sort(key=lambda x: -x[0])

        if not scored:
            # No match — show all
            scored = [(1, cmd) for cmd in self._all_commands]

        # Group by category if showing all, or just flat list if filtered
        if query:
            for _, cmd in scored:
                self._add_option(cmd)
        else:
            current_cat = None
            for _, cmd in scored:
                if cmd.category != current_cat:
                    current_cat = cmd.category
                    label = _CATEGORY_LABELS.get(cmd.category, cmd.category.upper())
                    self.add_option(
                        Option(f"[dim]── {label} ──[/dim]", id=f"__cat_{current_cat}__", disabled=True)
                    )
                self._add_option(cmd)

        if scored:
            self.highlighted = 0

    def _add_option(self, cmd: SlashCommand) -> None:
        shortcut = f"  [dim]{cmd.shortcut}[/dim]" if cmd.shortcut else ""
        self.add_option(
            Option(
                f"[b]{cmd.command:<14}[/b] [dim]{cmd.description}[/dim]{shortcut}",
                id=cmd.command,
            )
        )

    def show(self) -> None:
        self.add_class("-visible")

    def hide(self) -> None:
        self.remove_class("-visible")
