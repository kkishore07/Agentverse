"""
tui/screens/skills_screen.py
==============================
Plugin-based Skills Architecture Manager.
Displays capability cards with status, health, version, dependencies, and configuration.
"""

from __future__ import annotations

from dataclasses import dataclass
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Label, Static


@dataclass
class SkillInfo:
    id: str
    name: str
    icon: str
    version: str
    status: str
    health: str
    capabilities: str
    dependencies: str
    last_used: str
    description: str


BUILTIN_SKILLS = [
    SkillInfo("fs", "Filesystem", "📂", "2.1.0", "Enabled", "100%", "Read, Write, Edit, Rename, Move, Delete, Copy, Watch, Search", "OS VFS", "Just now", "Complete workspace file manipulation."),
    SkillInfo("term", "Terminal", "💻", "1.8.4", "Enabled", "100%", "Run, Kill, Background, Environment, History", "PowerShell / bash", "2 mins ago", "Terminal execution and environment management."),
    SkillInfo("git", "Git", "🌿", "2.4.0", "Enabled", "98%", "Status, Branch, Commit, Checkout, Push, Pull, Fetch, Merge, Diff, Log, Blame", "git >= 2.30", "15 mins ago", "Full version control suite."),
    SkillInfo("python", "Python", "🐍", "3.11", "Enabled", "100%", "Virtual Environment, Run Script, Install Packages, Format, Lint, Testing, Requirements", "python 3.11+", "1 hour ago", "Python toolchain and environment manager."),
    SkillInfo("pkg", "Package Managers", "📦", "1.5.0", "Enabled", "100%", "pip, uv, poetry, npm, pnpm, yarn, cargo, gradle, maven", "uv, npm, cargo", "Today", "Multi-ecosystem package management."),
    SkillInfo("docker", "Docker", "🐳", "24.0.5", "Disabled", "N/A", "Compose, Containers, Images, Volumes, Networks, Logs, Restart", "Docker Daemon", "Never", "Container orchestration and lifecycle."),
    SkillInfo("browser", "Browser", "🌍", "1.2.0", "Enabled", "95%", "Open URL, Download, Read Webpage, Workspace Search, Semantic Search, Regex Search", "Chromium", "Yesterday", "Automated web browsing & research."),
    SkillInfo("docs", "Documentation", "📝", "1.1.0", "Enabled", "100%", "README, API Docs, Markdown, Changelog", "Markdown engine", "3 days ago", "Documentation generation and parsing."),
    SkillInfo("test", "Testing", "🧪", "2.0.0", "Enabled", "100%", "Unit Tests, Integration Tests, Coverage, Benchmark", "pytest, unittest", "2 hours ago", "Automated testing and benchmark execution."),
    SkillInfo("sec", "Security", "🛡", "1.0.0", "Enabled", "100%", "Dependency Audit, Secret Scan, Static Analysis, License Check", "bandit, pip-audit", "Yesterday", "Vulnerability and dependency scanner."),
    SkillInfo("db", "Database", "🗄", "2.2.0", "Enabled", "100%", "SQLite, PostgreSQL, MySQL, MongoDB, Redis", "sqlite3 driver", "4 hours ago", "Database inspection and querying."),
    SkillInfo("intel", "Code Intelligence", "🔍", "3.1.0", "Enabled", "100%", "Find References, Rename Symbol, Go To Definition, Dependency Graph", "LSP Server", "Just now", "Language server intelligence & AST parsing."),
]


class SkillCard(Container):
    """Card widget for displaying skill metadata, status badge, and toggles."""

    DEFAULT_CSS = """
    SkillCard {
        height: 7;
        width: 100%;
        border: solid #2C2C2C;
        background: #171717;
        padding: 1;
        margin-bottom: 1;
    }

    SkillCard.-disabled {
        background: #111111;
        opacity: 0.6;
    }

    .sc-left {
        width: 30;
    }
    .sc-center {
        width: 1fr;
    }
    .sc-right {
        width: 20;
        align: right middle;
    }

    .sc-title {
        color: #ECECEC;
        text-style: bold;
        height: 1;
    }
    .sc-desc {
        color: #A5A5A5;
        height: 2;
    }
    .sc-meta {
        color: #A5A5A5;
        height: 1;
    }
    .sc-btn {
        height: 1;
        border: none;
        background: #1F1F1F;
        color: #ECECEC;
    }
    .sc-btn:hover {
        background: #3B82F6;
        color: #FFFFFF;
    }
    """

    def __init__(self, info: SkillInfo) -> None:
        self.info = info
        super().__init__(classes=f"skill-card {'-disabled' if info.status == 'Disabled' else ''}")

    def compose(self) -> ComposeResult:
        with Horizontal():
            with Vertical(classes="sc-left"):
                yield Label(f"{self.info.icon} {self.info.name}  [dim #A5A5A5]v{self.info.version}[/]", classes="sc-title")
                yield Label(self.info.description, classes="sc-desc")
                status_color = "#10B981" if self.info.status == "Enabled" else "#EF4444"
                yield Label(f"Health: [bold {status_color}]{self.info.health}[/] | Status: [bold {status_color}]{self.info.status}[/]", classes="sc-meta")

            with Vertical(classes="sc-center"):
                yield Label(f"[bold #3B82F6]Capabilities:[/] [dim #ECECEC]{self.info.capabilities}[/]", classes="sc-meta")
                yield Label(f"[bold #A5A5A5]Dependencies:[/] [dim #A5A5A5]{self.info.dependencies}[/]", classes="sc-meta")
                yield Label(f"[bold #A5A5A5]Last Used:[/] [dim #A5A5A5]{self.info.last_used}[/]", classes="sc-meta")

            with Vertical(classes="sc-right"):
                btn_text = "Disable" if self.info.status == "Enabled" else "Enable"
                yield Button(btn_text, id=f"toggle-{self.info.id}", classes="sc-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if self.info.status == "Enabled":
            self.info.status = "Disabled"
            self.info.health = "N/A"
            self.add_class("-disabled")
            event.button.label = "Enable"
        else:
            self.info.status = "Enabled"
            self.info.health = "100%"
            self.remove_class("-disabled")
            event.button.label = "Disable"


class SkillsScreen(ModalScreen[None]):
    """Comprehensive skill architecture manager."""

    BINDINGS = [Binding("escape", "dismiss_screen", "Close")]

    DEFAULT_CSS = """
    SkillsScreen {
        align: center middle;
        background: #090909 80%;
    }

    #skills-container {
        width: 85%;
        height: 85%;
        border: solid #3B82F6;
        background: #111111;
        padding: 1 2;
    }

    .s-header {
        height: 3;
        border-bottom: solid #2C2C2C;
        margin-bottom: 1;
    }

    .s-title {
        text-style: bold;
        color: #3B82F6;
        width: 1fr;
    }

    #s-scroll {
        height: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        with Container(id="skills-container"):
            with Horizontal(classes="s-header"):
                yield Label("⚡ Built-In Skill & Plugin Manager", classes="s-title")
                yield Label("Esc Close", classes="s-meta")
            with VerticalScroll(id="s-scroll"):
                for skill in BUILTIN_SKILLS:
                    yield SkillCard(skill)

    def action_dismiss_screen(self) -> None:
        self.dismiss()

    def on_key(self, event) -> None:
        if event.key in ("escape", "q"):
            self.dismiss()
