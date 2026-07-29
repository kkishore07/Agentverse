"""
tui/screens/splash_screen.py
===========================
Startup Splash Screen for DevPilot — Autonomous AI Software Development Team.
"""

from __future__ import annotations

import asyncio
from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.screen import ModalScreen
from textual.widgets import Static

SPLASH_ASCII = """\
██████╗ ███████╗██╗   ██╗██████╗ ██╗██╗      ██████╗ ████████╗
██╔══██╗██╔════╝██║   ██║██╔══██╗██║██║     ██╔═══██╗╚══██╔══╝
██║  ██║█████╗  ██║   ██║██████╔╝██║██║     ██║   ██║   ██║
██║  ██║██╔══╝  ╚██╗ ██╔╝██╔═══╝ ██║██║     ██║   ██║   ██║
██████╔╝███████╗ ╚████╔╝ ██║     ██║███████╗╚██████╔╝   ██║
╚═════╝ ╚══════╝  ╚═══╝  ╚═╝     ╚═╝╚══════╝ ╚═════╝    ╚═╝
"""

class SplashScreen(ModalScreen[None]):
    """Startup splash modal that simulates high-performance initialization."""

    DEFAULT_CSS = """
    SplashScreen {
        align: center middle;
        background: #0D1117;
    }

    #splash-container {
        width: 80;
        height: auto;
        padding: 2 3;
        border: solid #30363D;
        border-top: heavy #2F81F7;
        background: #161B22;
        align: center middle;
    }

    .splash-logo {
        color: #2F81F7;
        text-style: bold;
        text-align: center;
    }

    .splash-tagline {
        color: #56D364;
        text-align: center;
        margin-top: 1;
        text-style: bold;
    }

    .splash-subtitle {
        color: #7D8590;
        text-align: center;
        margin-bottom: 2;
        display: none;
    }

    .splash-status {
        color: #56D364;
        text-align: center;
        height: 1;
    }

    .splash-agents {
        color: #7D8590;
        text-align: center;
        margin-top: 1;
        height: 1;
        display: none;
    }
    """

    def compose(self) -> ComposeResult:
        with Container(id="splash-container"):
            yield Static(SPLASH_ASCII, classes="splash-logo")
            yield Static("AI Software Engineering Workspace", classes="splash-tagline")
            yield Static("", id="splash-status", classes="splash-status")

    def on_mount(self) -> None:
        self.run_worker(self._initialize())

    async def _initialize(self) -> None:
        status = self.query_one("#splash-status", Static)

        steps = [
            "Loading Models...",
            "Loading Agents...",
            "Loading Skills...",
            "Loading Workspace...",
        ]
        for step in steps:
            status.update(f"[bold #56D364]{step}[/]")
            await asyncio.sleep(0.3)
        await asyncio.sleep(0.25)
        self.dismiss()

    def on_key(self) -> None:
        self.dismiss()
