"""
core/agent_logger.py
====================
Structured Agent Logger for DevPilot v2.
Writes dedicated agent log files (Planner.log, Architect.log, Coder.log, Validator.log, Tester.log, Workspace.log).
"""

from __future__ import annotations

import datetime
from pathlib import Path
from typing import Any, Dict, Optional


class AgentLogger:
    """Manages structured timestamped logs for each agent."""

    def __init__(self, logs_dir: str | Path = "~/.devpilot/logs") -> None:
        self.logs_dir = Path(logs_dir).expanduser().resolve()
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    def get_log_path(self, agent_name: str) -> Path:
        filename = f"{agent_name.capitalize()}.log"
        return self.logs_dir / filename

    def log(self, agent_name: str, message: str, level: str = "INFO") -> None:
        path = self.get_log_path(agent_name)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level.upper()}] {message}\n"
        try:
            with open(path, "a", encoding="utf-8") as f:
                f.write(log_entry)
        except Exception:
            pass

    def log_failure(self, agent_name: str, details: Dict[str, Any]) -> None:
        path = self.get_log_path(agent_name)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lines = [
            f"==========================================================\n",
            f"[{timestamp}] [FAILURE] Agent: {agent_name}\n",
            f"Task: {details.get('task', 'N/A')}\n",
            f"Exception: [{details.get('exception_type', 'Error')}] {details.get('message', '')}\n",
            f"File: {details.get('affected_file', 'N/A')}:{details.get('affected_line', 'N/A')}\n",
            f"Command: {details.get('command_executed', 'N/A')} (Exit code: {details.get('exit_code', 'N/A')})\n",
            f"Suggestion: {details.get('suggestion', 'N/A')}\n",
        ]
        if details.get("stdout"):
            lines.append(f"--- STDOUT ---\n{details['stdout']}\n")
        if details.get("stderr"):
            lines.append(f"--- STDERR ---\n{details['stderr']}\n")
        lines.append("==========================================================\n")

        try:
            with open(path, "a", encoding="utf-8") as f:
                f.writelines(lines)
        except Exception:
            pass
