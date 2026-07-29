"""
ui/renderer.py
==============
EventBus → AppState bridge.
Subscribes to all events from core and pushes updates into AppState,
which triggers the prompt_toolkit app to redraw.
"""

from __future__ import annotations

from core.event_bus import (
    EventBus, Event,
    EVENT_AGENT_STARTED, EVENT_AGENT_STEP, EVENT_AGENT_FINISHED,
    EVENT_THINKING, EVENT_FILE_READING, EVENT_FILE_CREATING,
    EVENT_FILE_EDITING, EVENT_FILE_DELETING, EVENT_CODE_STREAM,
    EVENT_CODE_COMPLETE, EVENT_DIFF_READY, EVENT_FILE_CONFIRMED,
    EVENT_CHAT_TOKEN, EVENT_CHAT_COMPLETE, EVENT_TASK_STARTED,
    EVENT_TASK_COMPLETE, EVENT_ERROR, EVENT_WARNING, EVENT_STATUS,
)
from ui.app_state import AppState

# Agent icons
_AGENT_ICONS = {
    "Planner":       "🧠",
    "Architect":     "🏗",
    "Coder":         "💻",
    "Tester":        "🧪",
    "Documentation": "📚",
    "Git":           "🔀",
    "Reviewer":      "👁",
}


class LiveRenderer:
    """Translates EventBus events into AppState mutations."""

    def __init__(self, bus: EventBus, state: AppState) -> None:
        self._bus = bus
        self._state = state
        self._register()

    def _register(self):
        b = self._bus
        b.subscribe(EVENT_AGENT_STARTED,   self._on_agent_started)
        b.subscribe(EVENT_AGENT_STEP,      self._on_agent_step)
        b.subscribe(EVENT_AGENT_FINISHED,  self._on_agent_finished)
        b.subscribe(EVENT_THINKING,        self._on_thinking)
        b.subscribe(EVENT_FILE_READING,    self._on_file_reading)
        b.subscribe(EVENT_FILE_CREATING,   self._on_file_creating)
        b.subscribe(EVENT_FILE_EDITING,    self._on_file_editing)
        b.subscribe(EVENT_FILE_DELETING,   self._on_file_deleting)
        b.subscribe(EVENT_CODE_COMPLETE,   self._on_code_complete)
        b.subscribe(EVENT_DIFF_READY,      self._on_diff_ready)
        b.subscribe(EVENT_FILE_CONFIRMED,  self._on_file_confirmed)
        b.subscribe(EVENT_CHAT_TOKEN,      self._on_chat_token)
        b.subscribe(EVENT_CHAT_COMPLETE,   self._on_chat_complete)
        b.subscribe(EVENT_TASK_STARTED,    self._on_task_started)
        b.subscribe(EVENT_TASK_COMPLETE,   self._on_task_complete)
        b.subscribe(EVENT_ERROR,           self._on_error)
        b.subscribe(EVENT_WARNING,         self._on_warning)
        b.subscribe(EVENT_STATUS,          self._on_status)

    def _on_agent_started(self, event: Event):
        name = event.data.get("agent_name", "Agent")
        icon = _AGENT_ICONS.get(name, "🤖")
        self._state.start_agent(name, icon)
        self._state.add_message("agent", f"{icon} {name}", color="cyan", icon=icon)

    def _on_agent_step(self, event: Event):
        name = event.data.get("agent_name", "Agent")
        step = event.data.get("step", "")
        self._state.add_agent_step(name, f"✓ {step}")
        self._state.add_message("agent_step", f"  ✓ {step}", color="green")

    def _on_agent_finished(self, event: Event):
        name = event.data.get("agent_name", "Agent")
        self._state.finish_agent(name)
        self._state.add_message("agent_step", f"  ─────────────────────────────────", color="bright_black")

    def _on_thinking(self, event: Event):
        msg = event.data.get("message", "")
        self._state.add_message("agent_step", f"  🧠 {msg}", color="yellow")

    def _on_file_reading(self, event: Event):
        path = event.data.get("path", "")
        self._state.add_message("agent_step", f"  📖 Reading {path}", color="blue")

    def _on_file_creating(self, event: Event):
        path = event.data.get("path", "")
        self._state.add_message("agent_step", f"  📄 Creating {path}", color="cyan")

    def _on_file_editing(self, event: Event):
        path = event.data.get("path", "")
        self._state.add_message("agent_step", f"  ✏️  Editing {path}", color="magenta")

    def _on_file_deleting(self, event: Event):
        path = event.data.get("path", "")
        self._state.add_message("agent_step", f"  🗑️  Deleting {path}", color="red")

    def _on_code_complete(self, event: Event):
        path = event.data.get("path", "")
        content = event.data.get("content", "")
        self._state.last_generated_code[path] = content
        # Show the code as a formatted block
        lines = [
            f"\n  📄 {path}",
            "  " + "─" * 50,
        ]
        for line in content.splitlines()[:30]:  # preview first 30 lines
            lines.append(f"  {line}")
        if len(content.splitlines()) > 30:
            lines.append(f"  ... ({len(content.splitlines()) - 30} more lines)")
        lines.append("  " + "─" * 50)
        self._state.add_message("code", "\n".join(lines), color="bright_white")

    def _on_diff_ready(self, event: Event):
        path = event.data.get("path", "")
        diff = event.data.get("diff", "")
        self._state.last_diffs[path] = diff
        lines = [f"\n  📝 {path} (modified)", "  " + "─" * 50]
        for line in diff.splitlines()[:20]:
            if line.startswith("+"):
                lines.append(f"  \033[32m{line}\033[0m")
            elif line.startswith("-"):
                lines.append(f"  \033[31m{line}\033[0m")
            else:
                lines.append(f"  {line}")
        lines.append("  " + "─" * 50)
        self._state.add_message("diff", "\n".join(lines), color="bright_white")

    def _on_file_confirmed(self, event: Event):
        path = event.data.get("path", "")
        lines = event.data.get("lines", 0)
        functions = event.data.get("functions", 0)
        classes = event.data.get("classes", 0)
        imports = event.data.get("imports", 0)
        msg = (
            f"  ✓ {path}\n"
            f"    Lines     : {lines}\n"
            f"    Functions : {functions}\n"
            f"    Classes   : {classes}\n"
            f"    Imports   : {imports}"
        )
        self._state.add_message("confirm", msg, color="green")

    def _on_chat_token(self, event: Event):
        token = event.data.get("token", "")
        self._state.append_to_last_message(token)

    def _on_chat_complete(self, event: Event):
        self._state.set_status("Ready")

    def _on_task_started(self, event: Event):
        goal = event.data.get("goal", "")
        self._state.current_mode = "TASK"
        self._state.set_status("Running agents...")
        self._state.last_activity.clear()

    def _on_task_complete(self, event: Event):
        self._state.current_mode = "CHAT"
        files_created = event.data.get("files_created", [])
        files_modified = event.data.get("files_modified", [])
        goal = event.data.get("goal", "")
        elapsed = event.data.get("elapsed_seconds", 0)

        lines = [
            "",
            "  " + "═" * 50,
            f"  ✅ {goal}",
        ]
        if files_created:
            lines.append(f"  Files Created  : {', '.join(files_created)}")
        if files_modified:
            lines.append(f"  Files Modified : {', '.join(files_modified)}")
        lines.append(f"  Time           : {elapsed:.1f}s")
        lines.append("  " + "═" * 50)

        self._state.add_message("summary", "\n".join(lines), color="bright_green")
        self._state.set_status("Ready")

    def _on_error(self, event: Event):
        msg = event.data.get("message", "Unknown error")
        self._state.add_message("error", f"  ❌ {msg}", color="red")
        self._state.set_status("Error")

    def _on_warning(self, event: Event):
        msg = event.data.get("message", "")
        self._state.add_message("agent_step", f"  ⚠️  {msg}", color="yellow")

    def _on_status(self, event: Event):
        msg = event.data.get("message", "")
        self._state.set_status(msg)
