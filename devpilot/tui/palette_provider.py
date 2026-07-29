"""
tui/palette_provider.py
=========================
Fuzzy-searchable Textual command palette entries (Ctrl+P).
Surfaces all DevPilot actions + theme switching.
"""

from __future__ import annotations

from functools import partial

from textual.command import Hit, Hits, Provider

from tui.themes import THEMES


class DevPilotCommands(Provider):
    """Fuzzy-searchable palette entries for DevPilot's own actions."""

    async def search(self, query: str) -> Hits:
        matcher = self.matcher(query)
        app = self.app

        # Static action entries
        static_entries = [
            ("Show Agents",          "Browse and toggle pipeline agents",    app.action_show_agents),
            ("Show Models",          "Switch the active LLM model",          app.action_show_models),
            ("Show Skills",          "Browse and toggle skills",             app.action_show_skills),
            ("Show Settings",        "Edit DevPilot settings",               app.action_show_settings),
            ("Show Help",            "Keyboard shortcuts & commands",        app.action_show_help),
            ("Open Theme Picker",    "Switch color theme with live preview", app.action_show_themes),
            ("Clear Conversation",   "Erase the chat log",                   app.action_clear_chat),
            ("Focus Input",          "Move focus to the message input",      app.action_focus_input),
            ("Check Status",         "System health check (Ollama/model)",   app.action_check_status),
        ]

        for name, help_text, callback in static_entries:
            score = matcher.match(name)
            if score > 0:
                yield Hit(
                    score,
                    matcher.highlight(name),
                    partial(callback),
                    help=help_text,
                )

        # Dynamic theme-switch entries
        for display_name, tid in THEMES.items():
            entry_name = f"Theme: {display_name}"
            score = matcher.match(entry_name)
            if score > 0:
                theme_id = tid  # capture for closure

                async def _switch_theme(t: str = theme_id) -> None:
                    app.theme = t
                    app.notify(f"Theme: {display_name_for(t)}", title="Theme")

                from tui.themes import display_name_for
                yield Hit(
                    score,
                    matcher.highlight(entry_name),
                    partial(_switch_theme, tid),
                    help=f"Switch to the {display_name} color theme",
                )
