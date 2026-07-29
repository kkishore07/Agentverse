"""
tui/screens/splash_screen.py
===========================
Startup Splash Screen for DevPilot AI Engineering Workspace.
"""

from __future__ import annotations

import asyncio
from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.screen import ModalScreen
from textual.widgets import Static

SPLASH_ASCII = """
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
        background: #090909;
    }

    #splash-container {
        width: 70;
        height: auto;
        padding: 2;
        border: heavy #3B82F6;
        background: #111111;
        align: center middle;
    }

    .splash-logo {
        color: #3B82F6;
        text-style: bold;
        text-align: center;
    }

    .splash-subtitle {
        color: #A5A5A5;
        text-align: center;
        margin-bottom: 1;
        text-style: bold;
    }

    .splash-status {
        color: #10B981;
        text-align: center;
        height: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Container(id="splash-container"):
            yield Static(SPLASH_ASCII, classes="splash-logo")
            yield Static("AI Engineering Workspace v2.0", classes="splash-subtitle")
            yield Static("Initializing workspace...", id="splash-status", classes="splash-status")

    def on_mount(self) -> None:
        self.run_worker(self._initialize())

    async def _initialize(self) -> None:
        status = self.query_one("#splash-status", Static)
        steps = [
            "Loading UI...",
            "Loading Agents...",
            "Loading Models...",
            "Loading Skills...",
            "Loading Workspace...",
            "Loading Plugins...",
            "Loading Themes...",
            "Ready!",
        ]
        for step in steps:
            status.update(f"[bold #10B981]{step}[/]")
            await asyncio.sleep(0.12)
        await asyncio.sleep(0.3)
        self.dismiss()

    def on_key(self) -> None:
        self.dismiss()
