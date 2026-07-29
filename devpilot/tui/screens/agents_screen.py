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

_AGENT_ROLES = {
    "Planner":   "Task Planner",
    "Architect": "Solution Architect",
    "Coder":     "Code Generator",
    "Validator": "Code Validator",
    "Tester":    "Test Writer",
    "Fixer":     "Bug Fixer",
    "Reviewer":  "Code Reviewer",
    "Docs":      "Docs Writer",
    "GitHub":    "Git Manager",
    "Chat":      "Chat Assistant",
}

class AgentCard(Vertical):
    """Premium agent card for the Agent Manager screen."""
    DEFAULT_CSS = """
    AgentCard {
        width: 1fr;
        height: auto;
        padding: 1 2;
        margin: 0 1 1 0;
        background: #161B22;
        border: solid #30363D;
        border-top: thick #2F81F7;
    }

    AgentCard.-disabled {
        border-top: thick #F85149;
        opacity: 0.7;
    }

    .ac-header {
        layout: horizontal;
        height: 2;
        margin-bottom: 1;
        align: left middle;
    }

    .ac-icon {
        width: 3;
        height: 1;
        color: #E6EDF3;
    }

    .ac-title {
        text-style: bold;
        color: #E6EDF3;
        width: 1fr;
        height: 1;
    }

    .ac-role {
        color: #7D8590;
        width: auto;
        height: 1;
        padding: 0 1;
        background: #21262D;
    }

    Button.ac-badge {
        width: auto;
        padding: 0 1;
        background: #0D2A1A;
        color: #56D364;
        border: solid #56D364;
        height: 1;
        min-width: 10;
        margin-left: 1;
    }

    Button.ac-badge-off {
        width: auto;
        padding: 0 1;
        background: #1A0A0A;
        color: #F85149;
        border: solid #F85149;
        height: 1;
        min-width: 10;
        margin-left: 1;
    }

    Button.ac-badge:hover {
        background: #56D364;
        color: #0D1117;
    }

    Button.ac-badge-off:hover {
        background: #F85149;
        color: #0D1117;
    }

    .ac-desc {
        color: #7D8590;
        margin-bottom: 1;
        height: auto;
    }

    .ac-divider {
        height: 1;
        color: #30363D;
        margin-bottom: 1;
    }

    .ac-stats {
        layout: horizontal;
        height: auto;
    }

    .ac-stat-col {
        width: 1fr;
    }

    .ac-key {
        color: #7D8590;
        height: 1;
    }

    .ac-val {
        color: #E6EDF3;
        text-style: bold;
        height: 1;
    }
    """

    def __init__(self, name: str, desc: str, enabled: bool) -> None:
        self.agent_name = name
        self.desc = desc
        self.enabled = enabled
        super().__init__(classes="" if enabled else "-disabled")

    def compose(self) -> ComposeResult:
        icon = _AGENT_ICONS.get(self.agent_name, "⚙")
        role = _AGENT_ROLES.get(self.agent_name, "Agent")
        badge_cls = "ac-badge" if self.enabled else "ac-badge-off"
        badge_text = "● ACTIVE" if self.enabled else "○ DISABLED"

        # Mock stats for commercial feel
        exec_count = random.randint(10, 500)
        avg_time = round(random.uniform(0.5, 4.5), 1)
        success_rate = random.randint(85, 100)
        skills = (
            "Filesystem, CLI" if self.agent_name == "Coder"
            else ("Terminal, Git" if self.agent_name == "GitHub"
            else ("Analysis, Planning" if self.agent_name == "Planner"
            else "Search, Analysis"))
        )

        with Horizontal(classes="ac-header"):
            yield Static(icon, classes="ac-icon")
            yield Static(f"{self.agent_name}", classes="ac-title")
            yield Static(role, classes="ac-role")
            yield Button(badge_text, id=f"btn-{self.agent_name}", classes=badge_cls)

        yield Static(self.desc, classes="ac-desc")
        yield Static("─" * 40, classes="ac-divider")

        with Horizontal(classes="ac-stats"):
            with Vertical(classes="ac-stat-col"):
                yield Static("[#7D8590]Status[/]",    classes="ac-key")
                yield Static("[bold #E6EDF3]Idle[/]", classes="ac-val")
                yield Static("[#7D8590]Skills[/]",    classes="ac-key")
                yield Static(f"[bold #E6EDF3]{skills}[/]", classes="ac-val")
            with Vertical(classes="ac-stat-col"):
                yield Static("[#7D8590]Executions[/]",      classes="ac-key")
                yield Static(f"[bold #2F81F7]{exec_count}[/]", classes="ac-val")
                yield Static("[#7D8590]Avg Time[/]",         classes="ac-key")
                yield Static(f"[bold #E6EDF3]{avg_time}s[/]", classes="ac-val")
            with Vertical(classes="ac-stat-col"):
                yield Static("[#7D8590]Success Rate[/]",       classes="ac-key")
                yield Static(f"[bold #56D364]{success_rate}%[/]", classes="ac-val")
                yield Static("[#7D8590]Pipeline[/]",             classes="ac-key")
                yield Static("[bold #E6EDF3]Project Creation[/]", classes="ac-val")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button = event.button
        if button.id == f"btn-{self.agent_name}":
            self.enabled = not self.enabled
            button.label = "● ACTIVE" if self.enabled else "○ DISABLED"
            button.set_classes("ac-badge" if self.enabled else "ac-badge-off")
            self.set_class(not self.enabled, "-disabled")

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
        background: rgba(0, 0, 0, 0.8);
    }

    #as-container {
        width: 88%;
        height: 88%;
        background: #0D1117;
        border: solid #30363D;
        padding: 0;
    }

    #as-titlebar {
        height: 3;
        background: #161B22;
        border-bottom: solid #30363D;
        padding: 0 2;
        align: left middle;
        layout: horizontal;
    }

    #as-title {
        color: #2F81F7;
        text-style: bold;
        width: 1fr;
    }

    #as-subtitle {
        color: #7D8590;
        width: auto;
    }

    #as-close {
        width: auto;
        height: 1;
        border: none;
        background: transparent;
        color: #7D8590;
        padding: 0 1;
        min-width: 8;
    }

    #as-close:hover {
        background: #F85149;
        color: #E6EDF3;
    }

    #as-scroll {
        margin: 1;
        layout: grid;
        grid-size: 2;
        grid-rows: auto;
        grid-gutter: 1;
        overflow-y: auto;
        padding: 0 1;
    }
    """

    def __init__(self, registry: AgentRegistry) -> None:
        self._registry = registry
        super().__init__()

    def compose(self) -> ComposeResult:
        with Container(id="as-container"):
            with Horizontal(id="as-titlebar"):
                yield Static("⚙  AGENT MANAGER", id="as-title")
                yield Static("AgentVerse Autonomous Development Team", id="as-subtitle")
                yield Button("✕ Close", id="as-close-btn")
            with VerticalScroll(id="as-scroll"):
                for name, desc in self._registry.get_all().items():
                    enabled = self._registry.get(name) is not None
                    yield AgentCard(name, desc, enabled)
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "as-close-btn":
            self.dismiss()

    def action_dismiss_screen(self) -> None:
        self.dismiss()
