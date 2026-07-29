"""
tui/backend.py
==============
Bootstraps the non-UI runtime DevPilot needs: settings, the LLM client,
the event bus, the agent/skill registries, the session manager, and
workspace detection.

Kept separate from `tui/app.py` so the App class stays focused on
presentation. `Backend` is built once in `DevPilotApp.on_mount` and handed
down to every screen/widget that needs it — screens never construct their
own LLM client or registry, they receive this one (dependency injection,
same rule the original CLI followed).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from config import Settings, get_settings
from core.chat import ChatEngine
from core.event_bus import EventBus
from core.llm import OllamaLLMClient, build_default_llm_client
from core.registry import AgentRegistry, SkillRegistry
from core.router import IntentRouter
from core.session import SessionManager
from skills.filesystem import FilesystemSkill
from skills.terminal import TerminalSkill
from workspace.manager import WorkspaceDetector


@dataclass
class Backend:
    """Everything a screen/widget needs to talk to the real system."""

    settings: Settings
    llm: OllamaLLMClient
    bus: EventBus
    session_mgr: SessionManager
    agent_registry: AgentRegistry
    skill_registry: SkillRegistry
    chat_engine: ChatEngine
    router: IntentRouter
    workspace_info: dict[str, Any] = field(default_factory=dict)

    def rebuild_llm(self, model_name: str) -> None:
        """Swap the active model. Rebuilds the LLMClient and points the
        ChatEngine at it, so a model switch takes effect on the very next
        message without restarting the app."""
        self.settings.model_name = model_name
        self.llm = build_default_llm_client(self.settings)
        self.chat_engine = ChatEngine(self.llm)


# Human-readable metadata for the fixed pipeline agents. The Orchestrator
# always runs Planner -> Architect -> Coder (that's the pipeline's shape),
# but exposing them through AgentRegistry lets the Agents screen show their
# status and lets future agents (Security, Git, Docker, ...) register
# alongside them without changing this bootstrap code.
_AGENT_DESCRIPTIONS: dict[str, str] = {
    "Chat": "Main conversational interface and orchestrator integration.",
    "Planner": "Breaks a project request into ordered engineering tasks.",
    "Architect": "Designs folder structure, tech stack, and file manifest.",
    "Coder": "Generates the content of one source file at a time.",
    "Validator": "Validates source code against current architecture and standards.",
    "Tester": "Writes pytest coverage for generated source files.",
    "Fixer": "Analyzes test failures and automatically generates patches.",
    "Reviewer": "Reviews code changes before they are committed.",
    "Docs": "Writes project documentation (README, usage, structure).",
    "GitHub": "Manages Git repositories, commits, and pull requests.",
}


def build_backend() -> Backend:
    """Construct the full backend graph, mirroring what the previous
    prompt_toolkit console built in `interactive_loop()`."""
    settings = get_settings()
    settings.logs_dir.mkdir(parents=True, exist_ok=True)

    detector = WorkspaceDetector(settings.workspace_dir)
    workspace_info = detector.detect()

    llm = build_default_llm_client(settings)
    bus = EventBus()
    session_mgr = SessionManager(settings.data_dir / "session.json")

    agent_registry = AgentRegistry()
    for name, description in _AGENT_DESCRIPTIONS.items():
        agent_registry.register(name, description, enabled=True)

    skill_registry = SkillRegistry()
    skill_registry.register(
        "filesystem",
        FilesystemSkill(settings.workspace_dir, bus=bus),
        enabled=True,
    )
    skill_registry.register(
        "terminal",
        TerminalSkill(settings.workspace_dir),
        enabled=True,
    )

    chat_engine = ChatEngine(llm)
    router = IntentRouter()

    return Backend(
        settings=settings,
        llm=llm,
        bus=bus,
        session_mgr=session_mgr,
        agent_registry=agent_registry,
        skill_registry=skill_registry,
        chat_engine=chat_engine,
        router=router,
        workspace_info=workspace_info,
    )
