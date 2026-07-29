"""
ui/app_state.py
===============
Shared mutable state for the terminal UI.
All UI components read from / write to this single state object,
which is then used to invalidate and redraw the prompt_toolkit application.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional
from prompt_toolkit.application import Application


@dataclass
class Message:
    role: str          # "user", "assistant", "agent", "system"
    content: str
    color: str = "white"
    icon: str = ""


@dataclass
class AgentActivity:
    agent_name: str
    icon: str
    steps: list[str] = field(default_factory=list)
    active: bool = True


@dataclass
class AppState:
    """Single source of truth for all UI components."""

    # Conversation
    messages: list[Message] = field(default_factory=list)

    # Sidebar info
    workspace_name: str = ""
    workspace_language: str = "Unknown"
    workspace_file_count: int = 0
    git_branch: str = ""
    model_name: str = ""
    session_message_count: int = 0
    session_token_estimate: int = 0
    current_status: str = "Ready"

    # Agent panels (shown inline in conversation)
    active_agents: list[AgentActivity] = field(default_factory=list)

    # Bottom bar
    current_mode: str = "CHAT"  # "CHAT" or "TASK"
    active_agent_name: str = ""

    # Replay store
    last_plan: str = ""
    last_activity: list[str] = field(default_factory=list)
    last_generated_code: dict[str, str] = field(default_factory=dict)  # path -> content
    last_diffs: dict[str, str] = field(default_factory=dict)           # path -> diff

    # Reference back to the pt Application for invalidation
    app: Optional[Application] = field(default=None, repr=False)

    def invalidate(self):
        """Signal prompt_toolkit to redraw."""
        if self.app and not self.app.is_done:
            self.app.invalidate()

    def add_message(self, role: str, content: str, color: str = "white", icon: str = ""):
        self.messages.append(Message(role=role, content=content, color=color, icon=icon))
        self.session_message_count += 1
        self.session_token_estimate += len(content.split()) * 4 // 3  # rough estimate
        self.invalidate()

    def append_to_last_message(self, text: str):
        """Append streaming token to the last assistant message."""
        if self.messages and self.messages[-1].role == "assistant":
            self.messages[-1].content += text
            self.session_token_estimate += len(text.split()) * 4 // 3
            self.invalidate()

    def start_agent(self, agent_name: str, icon: str) -> AgentActivity:
        activity = AgentActivity(agent_name=agent_name, icon=icon)
        self.active_agents.append(activity)
        self.active_agent_name = agent_name
        self.current_status = f"{agent_name} running..."
        self.current_mode = "TASK"
        self.invalidate()
        return activity

    def add_agent_step(self, agent_name: str, step: str):
        for a in self.active_agents:
            if a.agent_name == agent_name and a.active:
                a.steps.append(step)
                self.last_activity.append(f"[{agent_name}] {step}")
                self.invalidate()
                return

    def finish_agent(self, agent_name: str):
        for a in self.active_agents:
            if a.agent_name == agent_name:
                a.active = False
        self.active_agent_name = ""
        self.current_status = "Ready"
        self.invalidate()

    def set_status(self, status: str):
        self.current_status = status
        self.invalidate()

    def clear(self):
        self.messages.clear()
        self.active_agents.clear()
        self.session_message_count = 0
        self.session_token_estimate = 0
        self.current_mode = "CHAT"
        self.invalidate()
