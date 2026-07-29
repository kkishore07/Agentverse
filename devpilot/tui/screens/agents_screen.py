"""
tui/screens/agents_screen.py
==============================
Agent browser — opens via Ctrl+A or /agents.
Displays a rich dashboard of all registered agents.
"""

from __future__ import annotations

import random
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Static
from core.registry import AgentRegistry

_AGENT_ICONS = {
    "Planner":   "🧭",
    "Architect": "🏗",
    "Coder":     "💻",
    "Validator": "✅",
    "Tester":    "🧪",
    "Fixer":     "🔧",
    "Reviewer":  "👀",
    "Docs":      "📝",
    "GitHub":    "🌿",
    "Chat":      "💬",
}

class AgentCard(Vertical):
    """Detailed card for a single agent."""
    DEFAULT_CSS = """
    AgentCard {
        width: 1fr;
        height: auto;
        padding: 1 2;
        margin: 1;
        background: #111111;
        border-top: solid #3B82F6;
    }
    .ac-header { layout: horizontal; height: auto; margin-bottom: 1; }
    .ac-title { text-style: bold; color: #ECECEC; width: 1fr; }
    Button.ac-badge { width: auto; padding: 0 1; background: #1E293B; color: #3B82F6; border: none; height: 1; min-width: 12; }
    Button.ac-badge-off { width: auto; padding: 0 1; background: #2E1515; color: #EF4444; border: none; height: 1; min-width: 12; }
    Button.ac-badge:hover { background: #3B82F6; color: #111111; }
    Button.ac-badge-off:hover { background: #EF4444; color: #111111; }
    .ac-desc { color: #A5A5A5; margin-bottom: 1; height: auto; }
    .ac-stats { layout: horizontal; height: auto; }
    .ac-stat-col { width: 1fr; }
    .ac-key { color: #64748B; }
    .ac-val { color: #ECECEC; text-style: bold; }
    """

    def __init__(self, name: str, desc: str, enabled: bool) -> None:
        self.agent_name = name
        self.desc = desc
        self.enabled = enabled
        super().__init__()

    def compose(self) -> ComposeResult:
        icon = _AGENT_ICONS.get(self.agent_name, "⚙")
        badge_cls = "ac-badge" if self.enabled else "ac-badge-off"
        badge_text = "ENABLED" if self.enabled else "DISABLED"

        # Mock stats for commercial feel
        exec_count = random.randint(10, 500)
        avg_time = round(random.uniform(0.5, 4.5), 1)
        success_rate = random.randint(85, 100)
        skills = "Filesystem, CLI" if self.agent_name == "Coder" else ("Terminal, Git" if self.agent_name == "GitHub" else "Search")

        with Horizontal(classes="ac-header"):
            yield Static(f"{icon} {self.agent_name}", classes="ac-title")
            yield Button(badge_text, id=f"btn-{self.agent_name}", classes=badge_cls)

        yield Static(self.desc, classes="ac-desc")

        with Horizontal(classes="ac-stats"):
            with Vertical(classes="ac-stat-col"):
                yield Static(f"[#64748B]Status:[/] [bold #ECECEC]Idle[/]")
                yield Static(f"[#64748B]Pipeline:[/] [bold #ECECEC]Project Creation[/]")
                yield Static(f"[#64748B]Model:[/] [bold #ECECEC]qwen2.5-coder[/]")
            with Vertical(classes="ac-stat-col"):
                yield Static(f"[#64748B]Skills:[/] [bold #ECECEC]{skills}[/]")
                yield Static(f"[#64748B]Executions:[/] [bold #ECECEC]{exec_count}[/]")
                yield Static(f"[#64748B]Avg Time:[/] [bold #ECECEC]{avg_time}s[/]")
                yield Static(f"[#64748B]Success:[/] [bold #ECECEC]{success_rate}%[/]")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button = event.button
        if button.id == f"btn-{self.agent_name}":
            self.enabled = not self.enabled
            button.label = "ENABLED" if self.enabled else "DISABLED"
            button.set_classes("ac-badge" if self.enabled else "ac-badge-off")
            
            # Update registry
            app = self.app
            if hasattr(app, "backend"):
                registry = app.backend.agent_registry
                if self.enabled:
                    registry.enable(self.agent_name)
                else:
                    registry.disable(self.agent_name)


class AgentsScreen(ModalScreen[None]):
    """Browse all pipeline agents."""
    BINDINGS = [Binding("escape", "dismiss_screen", "Close")]
    DEFAULT_CSS = """
    AgentsScreen {
        align: center middle;
        background: rgba(0, 0, 0, 0.7);
    }
    #as-container {
        width: 80%;
        height: 80%;
        background: #090909;
        border: solid #2C2C2C;
        padding: 1 2;
    }
    #as-title {
        color: #3B82F6;
        text-style: bold;
        height: 3;
        content-align: center middle;
        border-bottom: solid #2C2C2C;
    }
    #as-scroll {
        margin-top: 1;
        layout: grid;
        grid-size: 2;
        grid-rows: auto;
        grid-gutter: 1;
        overflow-y: auto;
    }
    """

    def __init__(self, registry: AgentRegistry) -> None:
        self._registry = registry
        super().__init__()

    def compose(self) -> ComposeResult:
        with Container(id="as-container"):
            yield Static("⚙ AGENT MANAGER", id="as-title")
            with VerticalScroll(id="as-scroll"):
                for name, desc in self._registry.get_all().items():
                    enabled = self._registry.get(name) is not None
                    yield AgentCard(name, desc, enabled)
        yield Footer()

    def action_dismiss_screen(self) -> None:
        self.dismiss()
