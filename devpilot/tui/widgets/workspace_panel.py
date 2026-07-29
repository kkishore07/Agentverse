"""
tui/widgets/workspace_panel.py
================================
Right-column panel: Workspace Inspector & System Telemetry.
Strictly metadata and system statistics — zero file tree elements.
"""

from __future__ import annotations

import time
from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll, Horizontal
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label, Static


class WorkspacePanel(VerticalScroll):
    """Right-column inspector panel displaying strictly metadata, system stats, and session state."""

    DEFAULT_CSS = """
    WorkspacePanel {
        width: 32;
        min-width: 25;
        max-width: 45;
        height: 100%;
        background: #111111;
        border-left: solid #2C2C2C;
        padding: 1;
    }

    .wp-section-title {
        text-style: bold;
        color: #3B82F6;
        border-bottom: solid #2C2C2C;
        margin-top: 1;
        margin-bottom: 1;
        padding-bottom: 0;
    }

    .wp-row {
        height: 1;
        color: #ECECEC;
    }

    .wp-key {
        color: #A5A5A5;
        width: 14;
    }

    .wp-val {
        color: #ECECEC;
        text-style: bold;
        width: 1fr;
    }

    .wp-val-accent {
        color: #10B981;
        text-style: bold;
        width: 1fr;
    }

    .wp-activity {
        color: #A5A5A5;
        height: auto;
        max-height: 8;
        background: #171717;
        padding: 1;
        margin-top: 1;
        border: solid #2C2C2C;
    }
    """

    project_name: reactive[str] = reactive("DevPilot")
    language: reactive[str] = reactive("Python")
    framework: reactive[str] = reactive("Textual")
    git_branch: reactive[str] = reactive("main")
    git_status: reactive[str] = reactive("Clean")

    model_name: reactive[str] = reactive("qwen2.5-coder:3b")
    context_length: reactive[str] = reactive("128K")
    token_usage: reactive[str] = reactive("1.4k / 128k")

    active_agent: reactive[str] = reactive("Coder")
    current_task: reactive[str] = reactive("Redesigning TUI")
    active_skill: reactive[str] = reactive("Filesystem")
    session_duration: reactive[str] = reactive("00:14:22")

    cpu_usage: reactive[str] = reactive("12%")
    ram_usage: reactive[str] = reactive("420 MB")

    theme_name: reactive[str] = reactive("DevPilot Dark")
    plugin_status: reactive[str] = reactive("8 Active")
    messages_count: reactive[int] = reactive(14)

    def compose(self) -> ComposeResult:
        # PROJECT INFO
        yield Static("PROJECT INSPECTOR", classes="wp-section-title")
        yield Static(f"[dim]Project:[/]    [bold #ECECEC]{self.project_name}[/]", classes="wp-row")
        yield Static(f"[dim]Language:[/]   [bold #ECECEC]{self.language}[/]", classes="wp-row")
        yield Static(f"[dim]Framework:[/]  [bold #ECECEC]{self.framework}[/]", classes="wp-row")
        yield Static(f"[dim]Git Branch:[/] [bold #3B82F6]{self.git_branch}[/]", classes="wp-row")
        yield Static(f"[dim]Git Status:[/] [bold #10B981]{self.git_status}[/]", classes="wp-row")

        # MODEL & AI SESSION
        yield Static("AI MODEL & SESSION", classes="wp-section-title")
        yield Static(f"[dim]Model:[/]      [bold #8B5CF6]{self.model_name}[/]", classes="wp-row", id="wp-model")
        yield Static(f"[dim]Context:[/]    [bold #ECECEC]{self.context_length}[/]", classes="wp-row")
        yield Static(f"[dim]Tokens:[/]     [bold #ECECEC]{self.token_usage}[/]", classes="wp-row", id="wp-tokens")
        yield Static(f"[dim]Messages:[/]   [bold #ECECEC]{self.messages_count}[/]", classes="wp-row", id="wp-msgs")

        # AGENT & EXECUTION
        yield Static("AGENT & EXECUTION", classes="wp-section-title")
        yield Static(f"[dim]Agent:[/]      [bold #F59E0B]{self.active_agent}[/]", classes="wp-row", id="wp-agent")
        yield Static(f"[dim]Task:[/]       [bold #ECECEC]{self.current_task}[/]", classes="wp-row", id="wp-task")
        yield Static(f"[dim]Skill:[/]      [bold #06B6D4]{self.active_skill}[/]", classes="wp-row", id="wp-skill")
        yield Static(f"[dim]Duration:[/]   [bold #ECECEC]{self.session_duration}[/]", classes="wp-row", id="wp-duration")

        # PIPELINE PROGRESS
        yield Static("PIPELINE PROGRESS", classes="wp-section-title")
        yield PipelineProgress(id="wp-pipeline")

        # LIVE FILE ACTIVITY
        yield Static("LIVE FILE ACTIVITY", classes="wp-section-title")
        yield LiveFileActivity(id="wp-file-activity")

        # SYSTEM & ENVIRONMENT
        yield Static("SYSTEM TELEMETRY", classes="wp-section-title")
        yield Static(f"[dim]CPU Usage:[/]  [bold #10B981]{self.cpu_usage}[/]", classes="wp-row")
        yield Static(f"[dim]RAM Usage:[/]  [bold #10B981]{self.ram_usage}[/]", classes="wp-row")
        yield Static(f"[dim]Theme:[/]      [bold #ECECEC]{self.theme_name}[/]", classes="wp-row", id="wp-theme")
        yield Static(f"[dim]Plugins:[/]    [bold #ECECEC]{self.plugin_status}[/]", classes="wp-row")

    def watch_active_skill(self, old_value: str, new_value: str) -> None:
        try:
            self.query_one("#wp-skill", Static).update(f"[dim]Skill:[/]      [bold #06B6D4]{new_value}[/]")
        except Exception:
            pass

    def update_agent(self, agent: str, task: str = "") -> None:
        self.active_agent = agent
        if task:
            self.current_task = task
        try:
            self.query_one("#wp-agent", Static).update(f"[dim]Agent:[/]      [bold #F59E0B]{agent}[/]")
            self.query_one("#wp-task", Static).update(f"[dim]Task:[/]       [bold #ECECEC]{self.current_task}[/]")
        except Exception:
            pass

    def update_model(self, model: str) -> None:
        self.model_name = model
        try:
            self.query_one("#wp-model", Static).update(f"[dim]Model:[/]      [bold #8B5CF6]{model}[/]")
        except Exception:
            pass

class BrailleSpinner(Static):
    FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    
    def __init__(self, **kwargs) -> None:
        super().__init__(self.FRAMES[0], **kwargs)
        self._frame = 0

    def on_mount(self) -> None:
        self._timer = self.set_interval(0.1, self.tick)

    def tick(self) -> None:
        self._frame = (self._frame + 1) % len(self.FRAMES)
        self.update(self.FRAMES[self._frame])


class PipelineProgress(Vertical):
    DEFAULT_CSS = """
    PipelineProgress {
        height: auto;
        padding: 0 1;
        margin: 0 0 1 0;
    }
    
    .pp-row {
        height: 1;
        layout: horizontal;
    }
    
    .pp-agent {
        width: 1fr;
        color: #A5A5A5;
    }
    
    .pp-agent-active {
        width: 1fr;
        color: #3B82F6;
        text-style: bold;
    }
    
    .pp-agent-done {
        width: 1fr;
        color: #ECECEC;
    }

    .pp-status {
        width: 3;
        text-align: right;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.agents = [
            "Planner",
            "Architect",
            "Coder",
            "Validator",
            "Tester",
            "Reviewer",
            "Documentation",
            "GitHub"
        ]
        self._statuses = {a: "○" for a in self.agents}

    def compose(self) -> ComposeResult:
        for agent in self.agents:
            with Horizontal(classes="pp-row", id=f"pp-row-{agent.lower()}"):
                yield Static(agent, classes="pp-agent", id=f"pp-name-{agent.lower()}")
                yield Static(self._statuses[agent], classes="pp-status", id=f"pp-status-{agent.lower()}")

    def set_agent_status(self, agent: str, status: str) -> None:
        agent = agent.replace("Agent", "").strip()
        if agent not in self.agents:
            return
        
        row = self.query_one(f"#pp-row-{agent.lower()}")
        name = self.query_one(f"#pp-name-{agent.lower()}", Static)
        status_lbl = self.query_one(f"#pp-status-{agent.lower()}", Static)

        if status == "running":
            name.classes = "pp-agent-active"
            status_lbl.update(BrailleSpinner())
            status_lbl.styles.color = "#3B82F6"
        elif status == "done":
            name.classes = "pp-agent-done"
            status_lbl.update("✔")
            status_lbl.styles.color = "#10B981"
        else:
            name.classes = "pp-agent"
            status_lbl.update("○")
            status_lbl.styles.color = "#A5A5A5"


class LiveFileActivity(VerticalScroll):
    DEFAULT_CSS = """
    LiveFileActivity {
        height: 8;
        background: #171717;
        padding: 0 1;
        margin-bottom: 1;
        border: solid #2C2C2C;
    }

    .lfa-row {
        height: 1;
        layout: horizontal;
    }

    .lfa-text {
        width: 1fr;
        color: #ECECEC;
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
        icon = "📖" if "read" in op.lower() else ("✏" if "update" in op.lower() or "edit" in op.lower() else ("➕" if "creat" in op.lower() else "🗑"))
        name = Static(f"{icon} {op} {Path(path).name}", classes="lfa-text")
        status = Static(BrailleSpinner(), classes="lfa-status")
        
        row.mount(name, status)
        self.mount(row)
        self.scroll_end(animate=False)
        self._activities[key] = status
        
    def finish_activity(self, path: str, op: str) -> None:
        key = f"{op}:{path}"
        if key in self._activities:
            status = self._activities[key]
            status.update("✓")
            status.styles.color = "#10B981"
