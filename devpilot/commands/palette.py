"""
commands/palette.py
===================
Slash command autocomplete palette for prompt_toolkit.
Typing '/' triggers inline autocomplete exactly like OpenCode.
"""

from __future__ import annotations

from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document


# Full command registry: name, description, aliases
COMMANDS = [
    ("/help",        "Show all available commands"),
    ("/exit",        "Quit DevPilot"),
    ("/clear",       "Clear the conversation"),
    ("/agents",      "Browse and toggle agents"),
    ("/models",      "Switch the active LLM model"),
    ("/skills",      "Browse and toggle skills"),
    ("/history",     "Show full conversation history"),
    ("/status",      "System health check"),
    ("/project",     "Show current workspace info"),
    ("/config",      "Show current configuration"),
    ("/show code",   "Reopen last generated code"),
    ("/show diff",   "Reopen last file diffs"),
    ("/show plan",   "Reopen last planner output"),
    ("/show activity","Replay implementation timeline"),
]


class CommandPalette(Completer):
    """prompt_toolkit Completer that activates when the input starts with '/'."""

    def get_completions(self, document: Document, complete_event):
        text = document.text_before_cursor
        if not text.startswith("/"):
            return

        typed = text.lower()
        for cmd, description in COMMANDS:
            if cmd.startswith(typed):
                # Show the part after what was already typed
                remaining = cmd[len(text):]
                display = f"{cmd:<22} {description}"
                yield Completion(
                    remaining,
                    start_position=0,
                    display=display,
                    display_meta=description,
                )
