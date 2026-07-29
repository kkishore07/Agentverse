"""
tui/themes.py
=============
AgentVerse ships nine curated dark themes. Custom themes (AgentVerse, Midnight,
Dracula, Cyberpunk) are bespoke `textual.theme.Theme` registrations that own
their full palette.

All themes are registered at import time via `register_theme()`. The rest
of the application only ever refers to the `THEMES` dict.
"""

from __future__ import annotations

from textual.theme import Theme


# ---------------------------------------------------------------------------
# Custom theme definitions
# ---------------------------------------------------------------------------

_AGENTVERSE = Theme(
    name="agentverse",
    dark=True,
    primary="#2F81F7",          # GitHub blue
    secondary="#8B5CF6",        # violet
    accent="#56D364",           # GitHub green
    background="#0D1117",       # GitHub dark canvas
    surface="#161B22",          # GitHub dark surface
    panel="#21262D",            # GitHub dark panel
    boost="#30363D",            # GitHub dark muted
    warning="#E3B341",          # amber
    error="#F85149",            # red
    success="#56D364",          # green
    foreground="#E6EDF3",       # primary text
    variables={
        "text": "#7D8590",              # muted text
        "border": "#30363D",
        "input-background": "#161B22",
        "scrollbar-color": "#30363D",
        "scrollbar-color-hover": "#2F81F7",
    },
)

_DEVPILOT_DARK = Theme(
    name="devpilot-dark",
    dark=True,
    primary="#3B82F6",          # blue accent
    secondary="#8B5CF6",        # purple accent
    accent="#06B6D4",           # cyan accent
    background="#090909",       # 90% black
    surface="#111111",          # dark surface
    panel="#171717",            # dark panel
    boost="#1F1F1F",            # secondary panel / selection
    warning="#F59E0B",          # orange warning
    error="#EF4444",            # red error
    success="#10B981",          # green success
    foreground="#ECECEC",       # primary text
    variables={
        "text": "#A5A5A5",       # muted text
        "border": "#2C2C2C",
        "input-background": "#111111",
        "scrollbar-color": "#2C2C2C",
        "scrollbar-color-hover": "#3B82F6",
    },
)

_MIDNIGHT = Theme(
    name="devpilot-midnight",
    dark=True,
    primary="#5B8AF5",          # electric blue
    secondary="#8B5CF6",        # violet
    accent="#38BDF8",           # sky cyan
    background="#090E1A",       # deep navy-black
    surface="#0F1629",          # slightly lighter navy
    panel="#131D35",            # card surface
    boost="#1A2540",            # hover / selection
    warning="#F59E0B",
    error="#F87171",
    success="#34D399",
    foreground="#E2E8F0",
    variables={
        "text": "#64748B",
        "border": "#1E2D4A",
        "input-background": "#0F1629",
        "scrollbar-color": "#1E2D4A",
        "scrollbar-color-hover": "#5B8AF5",
    },
)

_DRACULA = Theme(
    name="devpilot-dracula",
    dark=True,
    primary="#BD93F9",          # purple
    secondary="#FF79C6",        # pink
    accent="#8BE9FD",           # cyan
    background="#0D1117",       # darker than classic dracula
    surface="#161B22",
    panel="#1C2333",
    boost="#252F3F",
    warning="#FFB86C",
    error="#FF5555",
    success="#50FA7B",
    foreground="#F8F8F2",
    variables={
        "text": "#6272A4",
        "border": "#30363D",
        "input-background": "#161B22",
        "scrollbar-color": "#30363D",
        "scrollbar-color-hover": "#BD93F9",
    },
)

_CYBERPUNK = Theme(
    name="devpilot-cyberpunk",
    dark=True,
    primary="#00D4FF",          # neon cyan
    secondary="#FF006E",        # hot pink
    accent="#ADFF2F",           # lime
    background="#030712",       # near-black
    surface="#0A0F1E",
    panel="#0F1929",
    boost="#162038",
    warning="#FFD60A",
    error="#FF006E",
    success="#ADFF2F",
    foreground="#E2E8F0",
    variables={
        "text": "#475569",
        "border": "#162038",
        "input-background": "#0A0F1E",
        "scrollbar-color": "#162038",
        "scrollbar-color-hover": "#00D4FF",
    },
)


# ---------------------------------------------------------------------------
# Theme registry
# ---------------------------------------------------------------------------

# Display name → Textual theme id
# Order here drives the Theme picker / command palette.
THEMES: dict[str, str] = {
    "AgentVerse":       "agentverse",
    "DevPilot Dark":    "devpilot-dark",
    "Tokyo Night":       "tokyo-night",
    "Midnight":          "devpilot-midnight",
    "Catppuccin Mocha":  "catppuccin-mocha",
    "Nord":              "nord",
    "Gruvbox":           "gruvbox",
    "One Dark":          "atom-one-dark",
    "Dracula":           "devpilot-dracula",
    "Cyberpunk":         "devpilot-cyberpunk",
}

DEFAULT_THEME = "AgentVerse"

# Accent colour shown as a swatch in the theme picker (hex, for the preview dot)
THEME_ACCENTS: dict[str, str] = {
    "AgentVerse":       "#2F81F7",
    "DevPilot Dark":    "#3B82F6",
    "Tokyo Night":       "#7AA2F7",
    "Midnight":          "#5B8AF5",
    "Catppuccin Mocha":  "#CBA6F7",
    "Nord":              "#88C0D0",
    "Gruvbox":           "#FE8019",
    "One Dark":          "#61AFEF",
    "Dracula":           "#BD93F9",
    "Cyberpunk":         "#00D4FF",
}


def register_custom_themes(app) -> None:
    """Register bespoke themes with Textual's theme registry."""
    try:
        app.register_theme(_AGENTVERSE)
        app.register_theme(_DEVPILOT_DARK)
        app.register_theme(_MIDNIGHT)
        app.register_theme(_DRACULA)
        app.register_theme(_CYBERPUNK)
    except Exception:
        pass  # Themes might already be registered or unsupported


def theme_id(display_name: str) -> str:
    """Resolve a display name to Textual's internal theme id."""
    return THEMES.get(display_name, THEMES[DEFAULT_THEME])


def display_name_for(theme_id_value: str) -> str:
    """Reverse lookup: internal theme id → friendly display name."""
    for name, tid in THEMES.items():
        if tid == theme_id_value:
            return name
    return theme_id_value


def accent_for(display_name: str) -> str:
    """Return the hex accent colour used in the theme preview swatch."""
    return THEME_ACCENTS.get(display_name, "#2F81F7")
