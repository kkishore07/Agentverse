"""
tui/screens/command_palette.py
==============================
Floating Command Palette overlay (75% width, 60% height) using ListView for robust rendering.
Categorized into: Workspace, Agents, Models, Skills, Git, Settings, Plugins, History.
"""

from __future__ import annotations

from dataclasses import dataclass
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.screen import ModalScreen
from textual.widgets import Input, ListItem, ListView, Static


@dataclass
class CommandItem:
    id: str
    category: str
    icon: str
    title: str
    description: str
    shortcut: str = ""
    action: str = ""


COMMANDS = [
    # Navigation & Core
    CommandItem("chat",     "Workspace", ">", "Chat View",        "Open the main AI chat timeline", "Ctrl+L"),
    CommandItem("project",  "Workspace", "P", "Project Explorer", "Explore workspace files and git tree"),
    CommandItem("history",  "History",   "H", "Chat History",     "View past conversations & turns"),
    
    # AI Engine & Agents
    CommandItem("agents",   "Agents",    "A", "Manage Agents",    "Browse, select and configure AI agents", "Ctrl+A"),
    CommandItem("models",   "Models",    "M", "LLM Models",       "Switch active LLM model & provider", "Ctrl+M"),
    CommandItem("skills",   "Skills",    "S", "Skills & Plugins", "Manage system capabilities & tools", "Ctrl+S"),
    
    # Version Control
    CommandItem("status",   "Git",       "G", "Git Status",       "View branch status and working tree"),
    CommandItem("diff",     "Git",       "D", "Git Diff",         "Inspect uncommitted file changes"),
    
    # Configuration
    CommandItem("themes",   "Settings",  "T", "Themes",           "Live theme preview & color switcher", "Ctrl+T"),
    CommandItem("settings", "Settings",  "=", "Settings",         "Configure DevPilot preferences"),
    CommandItem("help",     "Settings",  "?", "Shortcuts Manual",  "View keyboard shortcuts guide", "Ctrl+H"),
    CommandItem("exit",     "Settings",  "X", "Exit DevPilot",    "Quit application safely", "Ctrl+Q"),
]


class DevPilotCommandPalette(ModalScreen[None]):
    """Floating command palette using ListView."""

    BINDINGS = [
        Binding("escape", "dismiss_screen", "Close"),
        Binding("down", "cursor_down", "Down"),
        Binding("up", "cursor_up", "Up"),
    ]

    DEFAULT_CSS = """
    DevPilotCommandPalette {
        align: center middle;
        background: #090909 80%;
    }

    DevPilotCommandPalette > Container {
        width: 75%;
        height: 60%;
        min-width: 60;
        max-width: 100;
        border: solid #3B82F6;
        background: #111111;
        padding: 1 2;
    }

    DevPilotCommandPalette Input {
        border: none;
        border-bottom: solid #3B82F6;
        background: #171717;
        height: 3;
        padding: 0 1;
        margin-bottom: 1;
        color: #ECECEC;
    }
    
    DevPilotCommandPalette Input:focus {
        border-bottom: thick #3B82F6;
    }

    DevPilotCommandPalette ListView {
        height: 1fr;
        border: solid #2C2C2C;
        background: #171717;
        padding: 1;
    }

    DevPilotCommandPalette ListItem {
        height: 3;
        padding: 0 1;
        color: #ECECEC;
    }
    
    DevPilotCommandPalette ListItem:hover {
        background: #1F1F1F;
    }

    DevPilotCommandPalette ListItem.-highlighted {
        background: #1F1F1F;
        border-left: thick #3B82F6;
    }
    """

    def compose(self) -> ComposeResult:
        with Container():
            yield Input(placeholder="Search commands... (e.g., 'model', 'agent', 'git')", id="cp-search")
            yield ListView(id="cp-list")

    async def on_mount(self) -> None:
        self.query_one("#cp-search", Input).focus()
        await self._populate_list("")

    async def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "cp-search":
            await self._populate_list(event.value)

    async def _populate_list(self, query: str) -> None:
        lst = self.query_one("#cp-list", ListView)
        await lst.clear()

        results = []
        for cmd in COMMANDS:
            if not query:
                score = 100
            else:
                q = query.lower().lstrip("/")
                if not q:
                    score = 100
                else:
                    title_lower = cmd.title.lower()
                    cat_lower = cmd.category.lower()
                    desc_lower = cmd.description.lower()
                    
                    if q in title_lower:
                        score = 100 - title_lower.index(q)
                    elif q in cat_lower:
                        score = 80 - cat_lower.index(q)
                    elif q in desc_lower:
                        score = 60
                    else:
                        score = 0

            if score > 0:
                results.append((score, cmd))

        results.sort(key=lambda x: x[0], reverse=True)

        for score, cmd in results:
            shortcut_str = f"[dim #A5A5A5]{cmd.shortcut}[/]" if cmd.shortcut else ""
            cmd_prefix = f"[dim #A5A5A5](/{cmd.id})[/]"
            label = f"[bold #3B82F6]{cmd.icon}[/]  [bold #ECECEC]{cmd.title:<14}[/] {cmd_prefix:<12} [dim #A5A5A5]{cmd.description:<35}[/] {shortcut_str}"
            
            item = ListItem(Static(label), name=cmd.id, id=f"cmd-{cmd.id}")
            await lst.append(item)

    def action_cursor_down(self) -> None:
        self.query_one("#cp-list", ListView).action_cursor_down()

    def action_cursor_up(self) -> None:
        self.query_one("#cp-list", ListView).action_cursor_up()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.item and hasattr(event.item, "name") and event.item.name:
            self.dismiss()
            app = self.app
            if hasattr(app, "_dispatch_slash"):
                app.run_worker(app._dispatch_slash(f"/{event.item.name}"))

    def action_dismiss_screen(self) -> None:
        self.dismiss()
