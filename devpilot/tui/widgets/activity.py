"""
tui/widgets/activity.py
========================
Live agent-activity display. Each agent run (Planner, Architect, Coder...)
gets its own `Collapsible` with an animated indeterminate `ProgressBar`
while running and a checklist of steps as they complete — replacing the
old approach of printing static Rich panels that had to be fully redrawn.

This widget doesn't call the LLM or the orchestrator itself; it only
reacts to `EventBus` events, which keeps it decoupled from *how* an agent
run was triggered (chat-mode task routing vs. a future `/create` command
both funnel through the same bus).
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.widgets import Collapsible, ProgressBar, Static


class AgentRunPanel(Vertical):
    """One collapsible block representing a single agent's run."""

    DEFAULT_CSS = """
    AgentRunPanel {
        height: auto;
        margin: 0 0 1 0;
    }
    AgentRunPanel .step-line {
        color: $foreground 50%;
        padding-left: 2;
    }
    AgentRunPanel .step-line.-latest {
        color: $success;
        text-style: bold;
    }
    """

    def __init__(self, agent_name: str, icon: str = "⚙") -> None:
        self.agent_name = agent_name
        self.icon = icon
        self._steps: list[str] = []
        super().__init__(id=f"agent-{_slug(agent_name)}")

    def compose(self) -> ComposeResult:
        with Collapsible(title=f"{self.icon} {self.agent_name} — running…", collapsed=False, id="collapsible"):
            yield ProgressBar(show_eta=False, id="progress")
            yield Static("", id="steps")

    def on_mount(self) -> None:
        self.query_one("#progress", ProgressBar).update(total=None)  # indeterminate

    def add_step(self, step: str) -> None:
        self._steps.append(step)
        # Keep the most recent step visually emphasized.
        lines = [f"  ✓ {s}" for s in self._steps[:-1]]
        if self._steps:
            lines.append(f"  › {self._steps[-1]}")
        self.query_one("#steps", Static).update("\n".join(lines))

    def finish(self, success: bool = True) -> None:
        collapsible = self.query_one("#collapsible", Collapsible)
        icon = "✓" if success else "✗"
        collapsible.title = f"{self.icon} {self.agent_name} — {icon} done"
        collapsible.collapsed = True
        progress = self.query_one("#progress", ProgressBar)
        progress.update(total=1, progress=1)


class ActivityLog(VerticalScroll):
    """Container holding one `AgentRunPanel` per agent run this session.

    Exposes `start_agent` / `add_step` / `finish_agent`, mirroring the old
    `AppState` API 1:1 so wiring it to `EventBus` callbacks is a drop-in
    replacement rather than a redesign of the event contract.
    """

    DEFAULT_CSS = """
    ActivityLog {
        height: auto;
        max-height: 16;
        border: round $primary-darken-1;
        padding: 0 1;
        margin: 0 0 1 0;
        display: none;
    }
    ActivityLog.-visible {
        display: block;
    }
    """

    def __init__(self) -> None:
        super().__init__(id="activity-log")
        self._panels: dict[str, AgentRunPanel] = {}

    def auto_scroll(self) -> None:
        if self.max_scroll_y - self.scroll_y <= 6:
            self.scroll_end(animate=True, duration=0.2)

    async def start_agent(self, agent_name: str, icon: str = "⚙") -> None:
        self.add_class("-visible")
        panel = AgentRunPanel(agent_name, icon)
        self._panels[agent_name] = panel
        await self.mount(panel)
        self.app.call_after_refresh(self.auto_scroll)

    def add_step(self, agent_name: str, step: str) -> None:
        panel = self._panels.get(agent_name)
        if panel is not None:
            panel.add_step(step)
            self.app.call_after_refresh(self.auto_scroll)

    def finish_agent(self, agent_name: str, success: bool = True) -> None:
        panel = self._panels.get(agent_name)
        if panel is not None:
            panel.finish(success=success)

    def reset(self) -> None:
        self._panels.clear()
        self.remove_children()
        self.remove_class("-visible")


def _slug(text: str) -> str:
    return "".join(c.lower() if c.isalnum() else "-" for c in text).strip("-")
