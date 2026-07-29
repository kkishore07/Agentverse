"""
config/__init__.py
==================
Centralized configuration for DevPilot.
Workspace auto-detects to cwd() so running `devpilot` inside any project
directory makes that project the active workspace.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import os


@dataclass
class Settings:
    """Mutable application settings (model can be switched at runtime)."""

    # --- LLM ---
    ollama_host: str = field(
        default_factory=lambda: os.getenv("DEVPILOT_OLLAMA_HOST", "http://localhost:11434")
    )
    model_name: str = field(
        default_factory=lambda: os.getenv("DEVPILOT_MODEL", "qwen2.5-coder:3b")
    )
    llm_timeout_seconds: int = field(
        default_factory=lambda: int(os.getenv("DEVPILOT_LLM_TIMEOUT", "180"))
    )
    llm_max_retries: int = field(
        default_factory=lambda: int(os.getenv("DEVPILOT_LLM_RETRIES", "3"))
    )
    llm_temperature: float = field(
        default_factory=lambda: float(os.getenv("DEVPILOT_TEMPERATURE", "0.2"))
    )

    # --- Paths ---
    # workspace_dir = current working directory so `devpilot` inside a project
    # detects that project, not the DevPilot install dir.
    workspace_dir: Path = field(default_factory=lambda: Path.cwd())
    logs_dir: Path = field(
        default_factory=lambda: Path.home() / ".devpilot" / "logs"
    )
    data_dir: Path = field(
        default_factory=lambda: Path.home() / ".devpilot"
    )

    # --- Behavior ---
    max_files_per_project: int = field(
        default_factory=lambda: int(os.getenv("DEVPILOT_MAX_FILES", "40"))
    )

    def ensure_dirs(self) -> None:
        """Create runtime directories if they don't already exist."""
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)


_settings: Settings | None = None


def get_settings() -> Settings:
    """Return the singleton Settings instance (created once per process)."""
    global _settings
    if _settings is None:
        _settings = Settings()
        _settings.ensure_dirs()
    return _settings


def update_model(model_name: str) -> None:
    """Hot-swap the active model without restarting."""
    s = get_settings()
    s.model_name = model_name
