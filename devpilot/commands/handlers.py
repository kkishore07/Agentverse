"""
commands/handlers.py
====================
Implementations for all slash commands.
Each handler receives the AppState and can mutate it to update the UI.
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ui.app_state import AppState
    from core.llm import OllamaLLMClient
    from config import Settings


async def cmd_help(state: "AppState", args: list[str], **_) -> None:
    from commands.palette import COMMANDS
    lines = ["\n  📋 Available Commands", "  " + "─" * 46]
    for cmd, desc in COMMANDS:
        lines.append(f"  {cmd:<22} {desc}")
    lines.append("")
    state.add_message("system", "\n".join(lines), color="bright_cyan")


async def cmd_exit(state: "AppState", **_) -> None:
    state.add_message("system", "\n  Goodbye! 👋\n", color="bright_cyan")
    state.invalidate()
    # Signal the main loop to stop
    raise SystemExit(0)


async def cmd_clear(state: "AppState", **_) -> None:
    state.clear()
    state.add_message("system", "  Conversation cleared.", color="bright_black")


async def cmd_status(state: "AppState", llm: "OllamaLLMClient", settings: "Settings", **_) -> None:
    reachable = await llm.is_reachable()
    ollama_status = "✓ Reachable" if reachable else "✗ Not reachable — is `ollama serve` running?"
    models = await llm.list_models() if reachable else []
    model_list = ", ".join(models[:5]) if models else "none found"

    lines = [
        "\n  🔍 System Status",
        "  " + "─" * 46,
        f"  Ollama        : {ollama_status}",
        f"  Active Model  : {settings.model_name}",
        f"  Models Found  : {model_list}",
        f"  Workspace     : {settings.workspace_dir}",
        f"  Status        : {state.current_status}",
        "",
    ]
    state.add_message("system", "\n".join(lines), color="bright_cyan")


async def cmd_project(state: "AppState", settings: "Settings", **_) -> None:
    from workspace.manager import WorkspaceDetector
    info = WorkspaceDetector(settings.workspace_dir).detect()
    lines = [
        "\n  📁 Workspace Info",
        "  " + "─" * 46,
        f"  Name       : {info['project_name']}",
        f"  Path       : {settings.workspace_dir}",
        f"  Language   : {info['language']}",
        f"  Framework  : {info['framework']}",
        f"  Files      : {info['file_count']}",
        f"  Git        : {'Yes' if info['git_detected'] else 'No'}",
        "",
    ]
    state.add_message("system", "\n".join(lines), color="bright_cyan")


async def cmd_config(state: "AppState", settings: "Settings", **_) -> None:
    lines = [
        "\n  ⚙️  Configuration",
        "  " + "─" * 46,
        f"  Model         : {settings.model_name}",
        f"  Ollama Host   : {settings.ollama_host}",
        f"  Timeout       : {settings.llm_timeout_seconds}s",
        f"  Max Retries   : {settings.llm_max_retries}",
        f"  Temperature   : {settings.llm_temperature}",
        f"  Max Files     : {settings.max_files_per_project}",
        f"  Workspace     : {settings.workspace_dir}",
        f"  Data Dir      : {settings.data_dir}",
        "",
    ]
    state.add_message("system", "\n".join(lines), color="bright_cyan")


async def cmd_models(state: "AppState", llm: "OllamaLLMClient", settings: "Settings", **_) -> None:
    reachable = await llm.is_reachable()
    if not reachable:
        state.add_message("error", "  ❌ Cannot reach Ollama. Is `ollama serve` running?", color="red")
        return

    models = await llm.list_models()
    if not models:
        state.add_message("system", "  No models found. Try `ollama pull qwen2.5-coder:3b`", color="yellow")
        return

    lines = ["\n  🤖 Installed Models", "  " + "─" * 46]
    for m in models:
        marker = "▶ " if m == settings.model_name else "  "
        lines.append(f"  {marker}{m}")
    lines.append("")
    lines.append("  To switch: /models <model-name>")
    lines.append("")
    state.add_message("system", "\n".join(lines), color="bright_cyan")


async def cmd_models_switch(state: "AppState", llm: "OllamaLLMClient", settings: "Settings", model_name: str, **_) -> None:
    from config import update_model
    update_model(model_name)
    llm._model = model_name
    state.model_name = model_name
    state.add_message("system", f"  ✓ Switched to model: {model_name}", color="green")


async def cmd_agents(state: "AppState", **_) -> None:
    agents = [
        ("🧠", "Planner",       "Breaks user requests into ordered tasks",          "enabled"),
        ("🏗",  "Architect",     "Designs folder structure and tech stack",           "enabled"),
        ("💻", "Coder",         "Generates code file-by-file",                       "enabled"),
        ("👁",  "Reviewer",      "Reviews code for bugs and improvements",            "enabled"),
        ("🧪", "Tester",        "Generates unit and integration tests",               "enabled"),
        ("📚", "Documentation", "Writes docstrings, READMEs, and comments",          "enabled"),
        ("🔀", "Git",           "Manages commits and branches (coming soon)",         "disabled"),
    ]
    lines = ["\n  🤖 Agent Registry", "  " + "─" * 56]
    for icon, name, desc, status in agents:
        status_str = "✓ enabled" if status == "enabled" else "✗ disabled"
        color_code = "" 
        lines.append(f"  {icon} {name:<16} {status_str:<12} {desc}")
    lines.append("")
    state.add_message("system", "\n".join(lines), color="bright_cyan")


async def cmd_skills(state: "AppState", **_) -> None:
    skills = [
        ("📁", "Filesystem",  "Read, write, and list files safely",    "enabled"),
        ("💻", "Terminal",    "Execute shell commands in workspace",    "enabled"),
        ("🐍", "Python",      "Run and analyze Python code",           "enabled"),
        ("🔀", "Git",         "Git operations (status, diff, commit)",  "disabled"),
        ("🌐", "Browser",     "Web browsing and scraping",              "disabled"),
        ("🐳", "Docker",      "Docker container management",            "disabled"),
    ]
    lines = ["\n  🛠 Skill Registry", "  " + "─" * 52]
    for icon, name, desc, status in skills:
        status_str = "✓ enabled" if status == "enabled" else "✗ disabled"
        lines.append(f"  {icon} {name:<14} {status_str:<12} {desc}")
    lines.append("")
    state.add_message("system", "\n".join(lines), color="bright_cyan")


async def cmd_history(state: "AppState", **_) -> None:
    if not state.messages:
        state.add_message("system", "  No conversation history yet.", color="bright_black")
        return
    lines = ["\n  📜 Conversation History", "  " + "─" * 46]
    for i, msg in enumerate(state.messages):
        if msg.role in ("user", "assistant"):
            prefix = "You" if msg.role == "user" else "DevPilot"
            preview = msg.content[:80].replace("\n", " ")
            if len(msg.content) > 80:
                preview += "..."
            lines.append(f"  [{i+1}] {prefix}: {preview}")
    lines.append("")
    state.add_message("system", "\n".join(lines), color="bright_cyan")


async def cmd_show_code(state: "AppState", **_) -> None:
    if not state.last_generated_code:
        state.add_message("system", "  No generated code in this session.", color="bright_black")
        return
    for path, content in state.last_generated_code.items():
        lines = [f"\n  📄 {path}", "  " + "─" * 50]
        for line in content.splitlines():
            lines.append(f"  {line}")
        lines.append("  " + "─" * 50)
        state.add_message("code", "\n".join(lines), color="bright_white")


async def cmd_show_diff(state: "AppState", **_) -> None:
    if not state.last_diffs:
        state.add_message("system", "  No diffs in this session.", color="bright_black")
        return
    for path, diff in state.last_diffs.items():
        lines = [f"\n  📝 {path}", "  " + "─" * 50]
        for line in diff.splitlines():
            lines.append(f"  {line}")
        lines.append("  " + "─" * 50)
        state.add_message("diff", "\n".join(lines), color="bright_white")


async def cmd_show_plan(state: "AppState", **_) -> None:
    if not state.last_plan:
        state.add_message("system", "  No planner output in this session.", color="bright_black")
        return
    state.add_message("system", f"\n  🧠 Last Plan\n  {'─'*50}\n{state.last_plan}\n", color="bright_cyan")


async def cmd_show_activity(state: "AppState", **_) -> None:
    if not state.last_activity:
        state.add_message("system", "  No agent activity in this session.", color="bright_black")
        return
    lines = ["\n  📋 Implementation Timeline", "  " + "─" * 50]
    for item in state.last_activity:
        lines.append(f"  {item}")
    lines.append("")
    state.add_message("system", "\n".join(lines), color="bright_cyan")
