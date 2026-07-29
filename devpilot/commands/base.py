"""
commands/base.py
================
Command dispatcher with full registry.
Routes slash command strings to their handler functions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ui.app_state import AppState
    from core.llm import OllamaLLMClient
    from config import Settings


async def handle_command(
    command_str: str,
    state: "AppState",
    llm: "OllamaLLMClient",
    settings: "Settings",
) -> None:
    """Parse and dispatch a slash command string."""
    from commands import handlers

    stripped = command_str.strip()
    parts = stripped.split(maxsplit=1)
    cmd = parts[0].lower() if parts else ""
    args = parts[1].split() if len(parts) > 1 else []

    ctx = dict(state=state, llm=llm, settings=settings, args=args)

    # /show <subcommand>
    if cmd == "/show":
        sub = args[0].lower() if args else ""
        if sub == "code":
            await handlers.cmd_show_code(**ctx)
        elif sub == "diff":
            await handlers.cmd_show_diff(**ctx)
        elif sub == "plan":
            await handlers.cmd_show_plan(**ctx)
        elif sub == "activity":
            await handlers.cmd_show_activity(**ctx)
        else:
            state.add_message("system", "  Usage: /show [code|diff|plan|activity]", color="yellow")
        return

    # /models <optional model name>
    if cmd == "/models":
        if args:
            await handlers.cmd_models_switch(model_name=args[0], **ctx)
        else:
            await handlers.cmd_models(**ctx)
        return

    dispatch = {
        "/help":     handlers.cmd_help,
        "/exit":     handlers.cmd_exit,
        "/clear":    handlers.cmd_clear,
        "/status":   handlers.cmd_status,
        "/project":  handlers.cmd_project,
        "/config":   handlers.cmd_config,
        "/agents":   handlers.cmd_agents,
        "/skills":   handlers.cmd_skills,
        "/history":  handlers.cmd_history,
    }

    handler = dispatch.get(cmd)
    if handler:
        await handler(**ctx)
    else:
        state.add_message(
            "system",
            f"  Unknown command: {cmd}  (type /help for all commands)",
            color="yellow",
        )
