"""
ui/console.py
=============
DevPilot v2 — Main entry point.

Implements a full-screen interactive terminal UI using prompt_toolkit.
Layout: Header | [Chat area | Sidebar] | Input bar

Design principles:
  - UI renders independently of business logic
  - All business logic communicates via EventBus
  - AppState is the single source of truth for all rendered text
  - Chat mode and Task mode are completely separate code paths
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.styles import Style
from prompt_toolkit.completion import ThreadedCompleter

from config import get_settings
from core.llm import build_default_llm_client
from core.chat import ChatEngine
from core.router import IntentRouter, Intent
from core.event_bus import EventBus, EVENT_CHAT_TOKEN, EVENT_TASK_STARTED, EVENT_TASK_COMPLETE
from core.session import SessionManager
from core.registry import SkillRegistry
from workspace.manager import WorkspaceDetector
from ui.app_state import AppState
from ui.renderer import LiveRenderer
from commands.base import handle_command
from commands.palette import CommandPalette


# ─── Styling ────────────────────────────────────────────────────────────────

STYLE = Style.from_dict({
    "prompt":          "bold #00d7ff",
    "prompt.indicator":"bold #ff5fd7",
    "completion-menu.completion":          "bg:#1a1a2e #e0e0e0",
    "completion-menu.completion.current":  "bg:#0d47a1 #ffffff bold",
    "completion-menu.meta.completion":     "bg:#1a1a2e #888888",
    "scrollbar.background":                "bg:#333333",
    "scrollbar.button":                    "bg:#888888",
})

# ─── Color helpers ───────────────────────────────────────────────────────────

_COLOR_MAP = {
    "white":        "\033[37m",
    "bright_white": "\033[97m",
    "cyan":         "\033[36m",
    "bright_cyan":  "\033[96m",
    "green":        "\033[32m",
    "bright_green": "\033[92m",
    "red":          "\033[31m",
    "bright_red":   "\033[91m",
    "yellow":       "\033[33m",
    "blue":         "\033[34m",
    "magenta":      "\033[35m",
    "bright_black": "\033[90m",
    "reset":        "\033[0m",
}

def colorize(text: str, color: str) -> str:
    code = _COLOR_MAP.get(color, "")
    reset = _COLOR_MAP["reset"]
    return f"{code}{text}{reset}"


# ─── Screen rendering ────────────────────────────────────────────────────────

def _clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def render_screen(state: AppState) -> None:
    """
    Full repaint of the terminal.
    Called after every state change.
    """
    _clear_screen()
    width = min(os.get_terminal_size().columns, 140)
    sidebar_width = 36
    chat_width = width - sidebar_width - 3  # 3 for separator + padding

    _render_header(state, width)
    _render_body(state, chat_width, sidebar_width)
    _render_bottom_bar(state, width)


def _render_header(state: AppState, width: int) -> None:
    title = " ★ DevPilot"
    subtitle = "AI Coding Assistant"
    model_info = f"[{state.model_name}]"
    branch = f"[{state.git_branch}]" if state.git_branch else ""
    right = f"{model_info} {branch}".strip()
    padding = width - len(title) - len(subtitle) - len(right) - 2
    header = (
        colorize("━" * width, "bright_black") + "\n"
        + colorize(title, "bright_cyan")
        + colorize(" " * max(1, (width // 2 - len(title) - len(subtitle) // 2)), "reset")
        + colorize(subtitle, "bright_black")
        + colorize(" " * max(1, padding), "reset")
        + colorize(right, "yellow")
        + "\n"
        + colorize("━" * width, "bright_black")
    )
    print(header)


def _render_body(state: AppState, chat_width: int, sidebar_width: int) -> None:
    chat_lines = _build_chat_lines(state, chat_width)
    sidebar_lines = _build_sidebar_lines(state, sidebar_width)

    # How many rows to show (fill terminal height minus header/footer)
    try:
        rows = max(10, os.get_terminal_size().lines - 10)
    except Exception:
        rows = 30

    # Trim to last N lines
    chat_lines = chat_lines[-(rows):]

    for i in range(rows):
        c = chat_lines[i] if i < len(chat_lines) else ""
        s = sidebar_lines[i] if i < len(sidebar_lines) else ""

        # Pad chat line
        visible_len = len(_strip_ansi(c))
        c_padded = c + " " * max(0, chat_width - visible_len)

        sep = colorize("│", "bright_black")
        print(f"{c_padded} {sep} {s}")


def _strip_ansi(text: str) -> str:
    import re
    return re.sub(r'\033\[[0-9;]*m', '', text)


def _build_chat_lines(state: AppState, width: int) -> list[str]:
    lines = []
    for msg in state.messages:
        if msg.role == "user":
            lines.append(colorize("", "reset"))
            lines.append(colorize("  You", "bright_cyan") + colorize(" ▸", "bright_black"))
            for line in msg.content.splitlines():
                lines.append(colorize(f"  {line}", "white"))
            lines.append("")
        elif msg.role == "assistant":
            lines.append(colorize("", "reset"))
            lines.append(colorize("  DevPilot", "bright_green") + colorize(" ▸", "bright_black"))
            for line in msg.content.splitlines():
                lines.append(colorize(f"  {line}", "white"))
            lines.append("")
        elif msg.role in ("agent", "agent_step", "code", "diff", "confirm", "summary", "error"):
            for line in msg.content.splitlines():
                color = msg.color or "white"
                lines.append(colorize(line, color))
        elif msg.role == "system":
            for line in msg.content.splitlines():
                lines.append(colorize(line, msg.color or "bright_black"))
    return lines


def _build_sidebar_lines(state: AppState, width: int) -> list[str]:
    def row(label: str, value: str, label_color="bright_black", val_color="white") -> str:
        return (
            colorize(f"  {label:<12}", label_color)
            + colorize(value[:width - 14], val_color)
        )

    lines = []
    lines.append(colorize(f"  {'WORKSPACE'}", "bright_cyan"))
    lines.append(colorize("  " + "─" * (width - 2), "bright_black"))
    lines.append(row("Project", state.workspace_name or "—"))
    lines.append(row("Language", state.workspace_language))
    lines.append(row("Files", str(state.workspace_file_count)))
    lines.append(row("Branch", state.git_branch or "—"))
    lines.append("")
    lines.append(colorize(f"  {'SESSION'}", "bright_cyan"))
    lines.append(colorize("  " + "─" * (width - 2), "bright_black"))
    lines.append(row("Model", state.model_name or "—", val_color="yellow"))
    lines.append(row("Messages", str(state.session_message_count)))
    lines.append(row("~Tokens", str(state.session_token_estimate)))
    lines.append(row("Status", state.current_status,
                       val_color="green" if state.current_status == "Ready" else "yellow"))
    lines.append("")
    lines.append(colorize(f"  {'AGENTS'}", "bright_cyan"))
    lines.append(colorize("  " + "─" * (width - 2), "bright_black"))

    agent_defs = [
        ("🧠", "Planner"), ("🏗",  "Architect"), ("💻", "Coder"),
        ("👁",  "Reviewer"), ("🧪", "Tester"),   ("📚", "Docs"),
    ]
    for icon, name in agent_defs:
        is_active = any(a.agent_name == name and a.active for a in state.active_agents)
        color = "bright_green" if is_active else "bright_black"
        marker = "▶ " if is_active else "  "
        lines.append(colorize(f"  {marker}{icon} {name}", color))

    return lines


def _render_bottom_bar(state: AppState, width: int) -> None:
    mode_color = "bright_green" if state.current_mode == "CHAT" else "bright_yellow"
    mode_str = colorize(f" {state.current_mode} ", mode_color)

    agent_str = ""
    if state.active_agent_name:
        agent_str = colorize(f" ◈ {state.active_agent_name} ", "bright_magenta")

    hint = colorize(" [/] commands  [Ctrl+C] exit ", "bright_black")
    model_str = colorize(f" {state.model_name} ", "yellow")

    bottom = colorize("━" * width, "bright_black")
    bar = mode_str + agent_str + model_str + hint
    print(bottom)
    print(bar)
    print(colorize("━" * width, "bright_black"))


# ─── Main loop ───────────────────────────────────────────────────────────────

async def interactive_loop() -> None:
    settings = get_settings()

    # Detect workspace
    detector = WorkspaceDetector(settings.workspace_dir)
    ws_info = detector.detect()

    # Initialize components
    llm = build_default_llm_client(settings)
    bus = EventBus()
    session_mgr = SessionManager(settings.data_dir / "session.json")
    skill_registry = SkillRegistry()

    # Shared UI state
    state = AppState()
    state.workspace_name = ws_info.get("project_name", "")
    state.workspace_language = ws_info.get("language", "Unknown")
    state.workspace_file_count = ws_info.get("file_count", 0)
    state.git_branch = ws_info.get("git_branch", "")
    state.model_name = settings.model_name

    # Wire event bus to state
    renderer = LiveRenderer(bus, state)

    # Chat engine and router
    chat_engine = ChatEngine(llm)
    router = IntentRouter()

    # Autocomplete
    completer = ThreadedCompleter(CommandPalette())

    # prompt_toolkit session
    prompt_session = PromptSession(
        history=InMemoryHistory(),
        completer=completer,
        style=STYLE,
        complete_while_typing=True,
    )

    # Initial welcome
    render_screen(state)
    state.add_message(
        "assistant",
        "Hello! I'm DevPilot, your AI coding assistant.\n"
        "  Type a question to chat, describe a task to build, or type / for commands.",
        color="white",
    )

    # ── Main REPL ──────────────────────────────────────────────────────────
    while True:
        try:
            render_screen(state)

            # Prompt line
            prompt_html = HTML(
                '<ansicyan><b>devpilot</b></ansicyan>'
                '<ansibrightblack> ❯ </ansibrightblack>'
            )
            with patch_stdout():
                user_input = await prompt_session.prompt_async(prompt_html)

            if not user_input.strip():
                continue

            text = user_input.strip()

            # ── Slash command ──────────────────────────────────────────────
            if text.startswith("/"):
                state.add_message("user", text)
                await handle_command(text, state=state, llm=llm, settings=settings)
                continue

            # ── Intent routing ─────────────────────────────────────────────
            state.add_message("user", text)
            intent = router.classify(text)

            if intent == Intent.CHAT:
                # ── Chat mode: stream response directly ────────────────────
                state.current_status = "Thinking..."
                state.add_message("assistant", "", color="white")
                render_screen(state)

                def on_token(token: str):
                    state.append_to_last_message(token)

                await chat_engine.respond_stream(text, on_token=on_token)
                state.current_status = "Ready"

            else:
                # ── Task mode: invoke orchestrator ─────────────────────────
                await _run_task(text, state, settings, llm, bus, skill_registry, session_mgr)

        except (EOFError, KeyboardInterrupt):
            print(colorize("\n\n  Goodbye! 👋\n", "bright_cyan"))
            break
        except SystemExit:
            break


async def _run_task(
    goal: str,
    state: AppState,
    settings,
    llm,
    bus: EventBus,
    skill_registry: SkillRegistry,
    session_mgr: SessionManager,
) -> None:
    """Run the full orchestrator pipeline for a TASK intent."""
    import time
    from core.orchestrator import Orchestrator
    from core.registry import AgentRegistry

    bus.publish(EVENT_TASK_STARTED, goal=goal)

    orchestrator = Orchestrator(
        llm=llm,
        session_mgr=session_mgr,
        event_bus=bus,
        skill_registry=skill_registry,
        agent_registry=AgentRegistry(),
        workspace_dir=settings.workspace_dir,
        max_files=settings.max_files_per_project,
    )

    start = time.monotonic()
    result = await orchestrator.run_pipeline("Project Creation", goal)
    elapsed = time.monotonic() - start

    files_created = [str(p) for p in (result.project_root.rglob("*.py") if result.success else [])]

    bus.publish(
        EVENT_TASK_COMPLETE,
        goal=goal,
        files_created=files_created[:6],
        files_modified=[],
        elapsed_seconds=elapsed,
        success=result.success,
    )


def main() -> None:
    """Entry point registered in pyproject.toml."""
    try:
        asyncio.run(interactive_loop())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
