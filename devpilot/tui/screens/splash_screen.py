"""
tui/screens/splash_screen.py
===========================
Startup Splash Screen for AgentVerse — Autonomous AI Software Development Team.
"""

from __future__ import annotations

import asyncio
from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.screen import ModalScreen
from textual.widgets import Static

SPLASH_ASCII = """\
    _                    _ __   __
   / \\   __ _  ___ _ __ | |\\ \\ / /__ _ __ ___  ___
  / _ \\ / _` |/ _ \\ '_ \\| __\\ V / _ \\ '__/ __|/ _ \\
 / ___ \\ (_| |  __/ | | | |_ | |  __/ |  \\__ \\  __/
/_/   \\_\\__, |\\___|_| |_|\\__||_|\\___|_|  |___/\\___|
        |___/
"""

class SplashScreen(ModalScreen[None]):
    """Startup splash modal that simulates high-performance initialization."""

    DEFAULT_CSS = """
    SplashScreen {
        align: center middle;
        background: #0D1117;
    }

    #splash-container {
        width: 66;
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
    }
    """

    def compose(self) -> ComposeResult:
        with Container(id="splash-container"):
            yield Static(SPLASH_ASCII, classes="splash-logo")
            yield Static("Autonomous AI Software Development Team", classes="splash-tagline")
            yield Static("Planner · Architect · Coder · Tester · Reviewer · Docs · GitHub", classes="splash-subtitle")
            yield Static("Initializing workspace...", id="splash-status", classes="splash-status")
            yield Static("", id="splash-agents", classes="splash-agents")

    def on_mount(self) -> None:
        self.run_worker(self._initialize())

    async def _initialize(self) -> None:
        status = self.query_one("#splash-status", Static)
        agents_label = self.query_one("#splash-agents", Static)

        steps = [
            ("Loading runtime...",      ""),
            ("Connecting to LLM...",    ""),
            ("Booting Planner...",      "🧭 Planner"),
            ("Booting Architect...",    "🏗 Architect"),
            ("Booting Coder...",        "💻 Coder"),
            ("Booting Tester...",       "🧪 Tester"),
            ("Loading workspace...",    ""),
            ("All systems ready!",      ""),
        ]
        for step, agent in steps:
            status.update(f"[bold #56D364]{step}[/]")
            if agent:
                agents_label.update(f"[dim #7D8590]{agent} online[/]")
            await asyncio.sleep(0.10)
        await asyncio.sleep(0.25)
        self.dismiss()

    def on_key(self) -> None:
        self.dismiss()
