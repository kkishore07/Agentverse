"""
tui/widgets/workspace_panel.py
================================
Right-column panel: Agent Team Dashboard & System Telemetry.

Displays:
- All 8 pipeline agents as rich cards with animated status
- Project metadata
- AI model & session info
- Live file activity feed
- System telemetry
"""

from __future__ import annotations

import time
from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll, Horizontal
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label, Static, ProgressBar


# ---------------------------------------------------------------------------
# BrailleSpinner — animated loading indicator
# ---------------------------------------------------------------------------

class BrailleSpinner(Static):
    """Animated braille spinner for running status."""
    FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def __init__(self, **kwargs) -> None:
        super().__init__(self.FRAMES[0], **kwargs)
        self._frame = 0

    def on_mount(self) -> None:
        self._timer = self.set_interval(0.1, self.tick)

    def tick(self) -> None:
        self._frame = (self._frame + 1) % len(self.FRAMES)
        self.update(self.FRAMES[self._frame])


# ---------------------------------------------------------------------------
# AgentStatusCard — premium card per agent
# ---------------------------------------------------------------------------

AGENT_ICONS = {
    "Planner":       "🧭",
    "Architect":     "🏗",
    "Coder":         "💻",
    "Validator":     "✅",
    "Tester":        "🧪",
    "Reviewer":      "👀",
    "Documentation": "📝",
    "GitHub":        "🌿",
}

AGENT_DESCRIPTIONS = {
    "Planner":       "Breaks goal into ordered tasks",
    "Architect":     "Designs folder & tech stack",
    "Coder":         "Generates source code files",
    "Validator":     "Validates code & standards",
    "Tester":        "Writes pytest test coverage",
    "Reviewer":      "Reviews code before commit",
    "Documentation": "Generates README & docs",
    "GitHub":        "Manages Git & pull requests",
}


class AgentStatusCard(Vertical):
    """Premium agent status card with icon, task, progress, and timer."""

    DEFAULT_CSS = """
    AgentStatusCard {
        height: auto;
        margin: 0 0 1 0;
        padding: 1 1;
        background: $panel;
        border-left: thick $panel;
    }

    AgentStatusCard.-running {
        border-left: thick $primary;
        background: $boost;
    }

    AgentStatusCard.-done {
        border-left: thick $success;
        background: $panel;
    }

    AgentStatusCard.-failed {
        border-left: thick $error;
        background: $panel;
    }

    AgentStatusCard.-waiting {
        border-left: thick $panel;
        background: $panel;
        opacity: 0.7;
    }

    .asc-header {
        height: 1;
        layout: horizontal;
        margin-bottom: 0;
    }

    .asc-icon {
        width: 3;
        color: $foreground 70%;
    }

    .asc-name {
        width: 1fr;
        color: $foreground 70%;
        text-style: bold;
    }

    .asc-name.-running {
        color: $primary;
        text-style: bold;
    }

    .asc-name.-done {
        color: $success;
    }

    .asc-name.-failed {
        color: $error;
    }

    .asc-status-dot {
        width: 3;
        text-align: right;
    }

    .asc-task {
        height: 1;
        color: $foreground 40%;
        padding-left: 3;
        margin-top: 0;
    }

    .asc-task.-running {
        color: $foreground 70%;
    }

    .asc-progress {
        height: 1;
        margin: 0 0 0 3;
        margin-top: 1;
    }

    AgentStatusCard ProgressBar {
        height: 1;
    }

    AgentStatusCard ProgressBar Bar {
        color: $primary;
        background: $boost;
    }

    AgentStatusCard.-done ProgressBar Bar {
        color: $success;
    }
    """

    def __init__(self, agent_name: str, **kwargs) -> None:
        self.agent_name = agent_name
        self._status = "waiting"   # waiting | running | done | failed
        self._task_text = AGENT_DESCRIPTIONS.get(agent_name, "Waiting...")
        self._start_time: float | None = None
        super().__init__(classes="agent-status-card -waiting", **kwargs)

    def compose(self) -> ComposeResult:
        icon = AGENT_ICONS.get(self.agent_name, "⚙")
        with Horizontal(classes="asc-header"):
            yield Static(icon, classes="asc-icon", id=f"asc-icon-{self.agent_name.lower()}")
            yield Static(self.agent_name, classes="asc-name", id=f"asc-name-{self.agent_name.lower()}")
            yield Static("○", classes="asc-status-dot", id=f"asc-dot-{self.agent_name.lower()}")
        yield Static(self._task_text, classes="asc-task", id=f"asc-task-{self.agent_name.lower()}")

    def set_status(self, status: str, task: str = "") -> None:
        """Update the agent card status: waiting | running | done | failed"""
        self._status = status
        if task:
            self._task_text = task[:35]

        # Update CSS classes
        self.set_class(status == "running", "-running")
        self.set_class(status == "done", "-done")
        self.set_class(status == "failed", "-failed")
        self.set_class(status == "waiting", "-waiting")

        # Update name label class
        try:
            name_lbl = self.query_one(f"#asc-name-{self.agent_name.lower()}", Static)
            name_lbl.set_class(status == "running", "-running")
            name_lbl.set_class(status == "done", "-done")
            name_lbl.set_class(status == "failed", "-failed")
        except Exception:
            pass

        # Update status dot
        try:
            dot = self.query_one(f"#asc-dot-{self.agent_name.lower()}", Static)
            if status == "running":
                dot.update("⠋")
                dot.styles.color = "#2F81F7"
                self._start_time = time.time()
                self.set_interval(0.1, self._spin_dot)
            elif status == "done":
                dot.update("✓")
                dot.styles.color = "#56D364"
            elif status == "failed":
                dot.update("✗")
                dot.styles.color = "#F85149"
            else:
                dot.update("○")
                dot.styles.color = "#7D8590"
        except Exception:
            pass

        # Update task text
        try:
            task_lbl = self.query_one(f"#asc-task-{self.agent_name.lower()}", Static)
            display_task = self._task_text if self._task_text else AGENT_DESCRIPTIONS.get(self.agent_name, "")
            task_lbl.update(display_task)
            task_lbl.set_class(status == "running", "-running")
        except Exception:
            pass

    _spin_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    _spin_idx = 0

    def _spin_dot(self) -> None:
        if self._status != "running":
            return
        self._spin_idx = (self._spin_idx + 1) % len(self._spin_frames)
        try:
            dot = self.query_one(f"#asc-dot-{self.agent_name.lower()}", Static)
            dot.update(self._spin_frames[self._spin_idx])
        except Exception:
            pass


# ---------------------------------------------------------------------------
# AgentTeamPanel — all 8 agent cards
# ---------------------------------------------------------------------------

class AgentTeamPanel(Vertical):
    """Displays all pipeline agents as status cards."""

    DEFAULT_CSS = """
    AgentTeamPanel {
        height: auto;
        margin: 0 0 1 0;
    }
    """

    AGENTS = [
        "Planner",
        "Architect",
        "Coder",
        "Validator",
        "Tester",
        "Reviewer",
        "Documentation",
        "GitHub",
    ]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._cards: dict[str, AgentStatusCard] = {}

    def compose(self) -> ComposeResult:
        for agent in self.AGENTS:
            card = AgentStatusCard(agent, id=f"agent-card-{agent.lower()}")
            self._cards[agent] = card
            yield card

    def set_agent_status(self, agent: str, status: str, task: str = "") -> None:
        # Normalize agent name (strip "Agent" suffix if present)
        agent = agent.replace("Agent", "").strip()
        # Try exact match first, then partial
        card = self._cards.get(agent)
        if card is None:
            for name, c in self._cards.items():
                if name.lower() in agent.lower() or agent.lower() in name.lower():
                    card = c
                    break
        if card:
            card.set_status(status, task)


# ---------------------------------------------------------------------------
# LiveFileActivity
# ---------------------------------------------------------------------------

class LiveFileActivity(VerticalScroll):
    """Live file activity feed showing creating/editing/reading operations."""

    DEFAULT_CSS = """
    LiveFileActivity {
        height: 7;
        background: $background;
        padding: 0 1;
        margin-bottom: 1;
        border: solid $panel;
    }

    .lfa-row {
        height: 1;
        layout: horizontal;
    }

    .lfa-text {
        width: 1fr;
        color: $foreground 70%;
    }

    .lfa-status {
        width: 3;
        text-align: right;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._activities = {}

    def add_activity(self, path: str, op: str) -> None:
        key = f"{op}:{path}"
        if key in self._activities:
            return

        row = Horizontal(classes="lfa-row")
        if "read" in op.lower():
            icon = "📖"
            color = "#7D8590"
        elif "updat" in op.lower() or "edit" in op.lower():
            icon = "✏"
            color = "#E3B341"
        elif "creat" in op.lower():
            icon = "+"
            color = "#56D364"
        else:
            icon = "🗑"
            color = "#F85149"

        short_name = Path(path).name
        name = Static(f"[{color}]{icon}[/] {short_name}", classes="lfa-text")
        status = Static("⠋", classes="lfa-status")
        status.styles.color = "#2F81F7"

        row.mount(name, status)
        self.mount(row)
        self.scroll_end(animate=False)
        self._activities[key] = status

    def finish_activity(self, path: str, op: str) -> None:
        key = f"{op}:{path}"
        if key in self._activities:
            status = self._activities[key]
            status.update("✓")
            status.styles.color = "#56D364"


# ---------------------------------------------------------------------------
# WorkspacePanel — main right sidebar
# ---------------------------------------------------------------------------

class WorkspacePanel(VerticalScroll):
    """Right-column panel: Agent Team Dashboard, telemetry, and session state."""

    DEFAULT_CSS = """
    WorkspacePanel {
        width: 34;
        min-width: 28;
        max-width: 48;
        height: 100%;
        background: $surface;
        border-left: solid $panel;
        padding: 0;
    }

    .wp-section-header {
        text-style: bold;
        color: $foreground 50%;
        border-bottom: solid $panel;
        padding: 0 1;
        margin-top: 1;
        margin-bottom: 0;
        height: 2;
        align: left middle;
    }

    .wp-section-body {
        padding: 1 1;
    }

    .wp-row {
        height: 1;
        color: $foreground 80%;
        layout: horizontal;
    }

    .wp-key {
        color: $foreground 40%;
        width: 13;
    }

    .wp-val {
        color: $foreground;
        text-style: bold;
        width: 1fr;
    }

    .wp-val-blue {
        color: $primary;
        text-style: bold;
        width: 1fr;
    }

    .wp-val-green {
        color: $success;
        text-style: bold;
        width: 1fr;
    }

    .wp-val-purple {
        color: $secondary;
        text-style: bold;
        width: 1fr;
    }

    .wp-val-amber {
        color: $warning;
        text-style: bold;
        width: 1fr;
    }
    """

    project_name: reactive[str] = reactive("AgentVerse")
    language: reactive[str] = reactive("Python")
    framework: reactive[str] = reactive("Textual")
    git_branch: reactive[str] = reactive("main")
    git_status: reactive[str] = reactive("Clean")

    model_name: reactive[str] = reactive("qwen2.5-coder:3b")
    context_length: reactive[str] = reactive("128K")
    token_usage: reactive[str] = reactive("0 / 128k")

    active_agent: reactive[str] = reactive("—")
    current_task: reactive[str] = reactive("Waiting for task...")
    active_skill: reactive[str] = reactive("—")
    session_duration: reactive[str] = reactive("00:00:00")

    cpu_usage: reactive[str] = reactive("—")
    ram_usage: reactive[str] = reactive("—")

    theme_name: reactive[str] = reactive("AgentVerse")
    plugin_status: reactive[str] = reactive("8 Active")
    messages_count: reactive[int] = reactive(0)

    def compose(self) -> ComposeResult:
        # ── AGENTVERSE BRANDING ──────────────────────────────
        yield Static(" ◈ AGENTVERSE", classes="wp-section-header")

        with Vertical(classes="wp-section-body"):
            yield Static("[dim]Autonomous AI Software Development Team[/]", classes="wp-row")

        # ── AGENT TEAM ───────────────────────────────────────
        yield Static(" ⚙ AGENT TEAM", classes="wp-section-header")
        yield AgentTeamPanel(id="wp-agent-team")

        # ── LIVE FILE ACTIVITY ───────────────────────────────
        yield Static(" 📁 FILE ACTIVITY", classes="wp-section-header")
        yield LiveFileActivity(id="wp-file-activity")

        # ── PROJECT INFO ─────────────────────────────────────
        yield Static(" 📂 PROJECT", classes="wp-section-header")
        with Vertical(classes="wp-section-body"):
            with Horizontal(classes="wp-row"):
                yield Static("Name", classes="wp-key")
                yield Static(self.project_name, classes="wp-val", id="wp-project")
            with Horizontal(classes="wp-row"):
                yield Static("Language", classes="wp-key")
                yield Static(self.language, classes="wp-val", id="wp-language")
            with Horizontal(classes="wp-row"):
                yield Static("Framework", classes="wp-key")
                yield Static(self.framework, classes="wp-val", id="wp-framework")
            with Horizontal(classes="wp-row"):
                yield Static("Branch", classes="wp-key")
                yield Static(self.git_branch, classes="wp-val-blue", id="wp-branch")
            with Horizontal(classes="wp-row"):
                yield Static("Status", classes="wp-key")
                yield Static(self.git_status, classes="wp-val-green", id="wp-git-status")

        # ── AI MODEL & SESSION ───────────────────────────────
        yield Static(" ◈ MODEL & SESSION", classes="wp-section-header")
        with Vertical(classes="wp-section-body"):
            with Horizontal(classes="wp-row"):
                yield Static("Model", classes="wp-key")
                yield Static(self.model_name, classes="wp-val-purple", id="wp-model")
            with Horizontal(classes="wp-row"):
                yield Static("Context", classes="wp-key")
                yield Static(self.context_length, classes="wp-val", id="wp-context")
            with Horizontal(classes="wp-row"):
                yield Static("Tokens", classes="wp-key")
                yield Static(self.token_usage, classes="wp-val", id="wp-tokens")
            with Horizontal(classes="wp-row"):
                yield Static("Messages", classes="wp-key")
                yield Static(str(self.messages_count), classes="wp-val", id="wp-msgs")

        # ── ACTIVE EXECUTION ─────────────────────────────────
        yield Static(" ⚡ EXECUTION", classes="wp-section-header")
        with Vertical(classes="wp-section-body"):
            with Horizontal(classes="wp-row"):
                yield Static("Agent", classes="wp-key")
                yield Static(self.active_agent, classes="wp-val-amber", id="wp-agent")
            with Horizontal(classes="wp-row"):
                yield Static("Task", classes="wp-key")
                yield Static(self.current_task, classes="wp-val", id="wp-task")
            with Horizontal(classes="wp-row"):
                yield Static("Skill", classes="wp-key")
                yield Static(self.active_skill, classes="wp-val-blue", id="wp-skill")

        # ── SYSTEM TELEMETRY ─────────────────────────────────
        yield Static(" 📊 TELEMETRY", classes="wp-section-header")
        with Vertical(classes="wp-section-body"):
            with Horizontal(classes="wp-row"):
                yield Static("CPU", classes="wp-key")
                yield Static(self.cpu_usage, classes="wp-val-green", id="wp-cpu")
            with Horizontal(classes="wp-row"):
                yield Static("RAM", classes="wp-key")
                yield Static(self.ram_usage, classes="wp-val-green", id="wp-ram")
            with Horizontal(classes="wp-row"):
                yield Static("Theme", classes="wp-key")
                yield Static(self.theme_name, classes="wp-val", id="wp-theme")
            with Horizontal(classes="wp-row"):
                yield Static("Plugins", classes="wp-key")
                yield Static(self.plugin_status, classes="wp-val", id="wp-plugins")

    # ---- Update Methods ------------------------------------------------

    def watch_active_skill(self, old_value: str, new_value: str) -> None:
        try:
            self.query_one("#wp-skill", Static).update(new_value or "—")
        except Exception:
            pass

    def update_agent(self, agent: str, task: str = "") -> None:
        self.active_agent = agent
        if task:
            self.current_task = task
        try:
            self.query_one("#wp-agent", Static).update(agent or "—")
            self.query_one("#wp-task", Static).update((self.current_task[:30] + "…") if len(self.current_task) > 30 else self.current_task)
        except Exception:
            pass
        # Also update agent team panel
        try:
            panel = self.query_one("#wp-agent-team", AgentTeamPanel)
            panel.set_agent_status(agent, "running", task)
        except Exception:
            pass

    def update_model(self, model: str) -> None:
        self.model_name = model
        try:
            short = model.split(":")[0] if ":" in model else model
            self.query_one("#wp-model", Static).update(short)
        except Exception:
            pass
