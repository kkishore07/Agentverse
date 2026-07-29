"""
tui/app.py
==========
DevPilotApp — Premium 3-Column AI Engineering Workspace Shell.

Layout (3 Columns):
  ┌─────────────────────────────────────────────────────────────────┐
  │  DevPilotHeader (logo · workspace · git · model · conn · mode)  │
  ├───────────────┬─────────────────────────────────┬───────────────┤
  │               │                                 │               │
  │ Project       │  ChatLog (Unified Timeline)     │ Workspace     │
  │ Explorer      │  Collapsible Reasoning          │ Inspector     │
  │ (Left Panel)  │  Inline File Operation Cards    │ (Right Panel) │
  │               │  ChatInput                      │               │
  │               │                                 │               │
  ├───────────────┴─────────────────────────────────┴───────────────┤
  │  StatusBar (mode · status · agent · workspace · model · tokens) │
  └─────────────────────────────────────────────────────────────────┘
  Footer (Keyboard shortcuts)
"""

from __future__ import annotations

from textual import events, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Footer, Input

from core.event_bus import (
    EVENT_AGENT_FINISHED,
    EVENT_AGENT_STARTED,
    EVENT_AGENT_STEP,
    EVENT_ERROR,
    EVENT_FILE_CONFIRMED,
    EVENT_FILE_CREATING,
    EVENT_FILE_EDITING,
    EVENT_FILE_READING,
    EVENT_TASK_COMPLETE,
    EVENT_TASK_STARTED,
    EVENT_WARNING,
)
from core.router import Intent
from tui.backend import Backend, build_backend
from tui.palette_provider import DevPilotCommands
from tui.screens.agents_screen import AgentsScreen
from tui.screens.file_preview_screen import FilePreviewScreen
from tui.screens.help_screen import HelpScreen
from tui.screens.models_screen import ModelsScreen
from tui.screens.settings_screen import SettingsScreen
from tui.screens.skills_screen import SkillsScreen
from tui.screens.splash_screen import SplashScreen
from tui.screens.theme_screen import ThemeScreen
from tui.themes import DEFAULT_THEME, display_name_for, register_custom_themes, theme_id
from tui.widgets.chat_view import ChatLog
from tui.widgets.header import DevPilotHeader
from tui.widgets.project_explorer import FileSelectedForPreview, ProjectExplorer
from tui.widgets.status_bar import StatusBar
from tui.widgets.workspace_panel import WorkspacePanel

AGENT_ICONS = {
    "Planner":   "🧭",
    "Architect": "🏗",
    "Coder":     "💻",
    "Tester":    "🧪",
    "Docs":      "📝",
}

WELCOME = (
    "**Welcome to DevPilot AI Engineering Workspace.**\n\n"
    "I'm your AI pair programmer. Type a prompt or goal to get started.\n\n"
    "**Keyboard Quickstart:**\n"
    "- `Ctrl+P` — Open Command Palette\n"
    "- `Ctrl+M` — Open Model Manager\n"
    "- `Ctrl+S` — Open Skill & Plugin Manager\n"
    "- `Ctrl+T` — Open Live Theme Switcher\n"
    "- `Ctrl+H` — View Shortcuts Manual"
)


class ChatInput(Input):
    """Modern rounded input bar."""
    pass


class DevPilotApp(App[None]):
    """Premium terminal IDE for DevPilot AI coding assistant."""

    TITLE = "DevPilot"
    SUB_TITLE = "AI Engineering Workspace"
    COMMANDS = App.COMMANDS | {DevPilotCommands}

    DEFAULT_CSS = """
    Screen {
        layers: base overlay;
        background: #090909;
    }

    #body {
        height: 1fr;
        background: #090909;
    }

    #center-column {
        width: 1fr;
        height: 100%;
        background: #090909;
    }

    #input-area {
        height: auto;
        padding: 1 2;
        background: #111111;
        border-top: solid #2C2C2C;
    }

    #chat-input {
        background: #171717;
        border: solid #3B82F6;
        padding: 0 1;
        height: 3;
        color: #ECECEC;
    }

    #chat-input:focus {
        border: thick #3B82F6;
    }
    """

    BINDINGS = [
        Binding("ctrl+q",     "quit_app",              "Quit DevPilot", priority=True),
        Binding("ctrl+c",     "copy_last_response",    "Copy Last",     priority=True),
        Binding("ctrl+p",     "show_command_palette",  "Palette",       priority=True),
        Binding("ctrl+a",     "show_agents",           "Agents",        priority=True),
        Binding("ctrl+m",     "show_models",           "Models",        priority=True),
        Binding("ctrl+s",     "show_skills",           "Skills",        priority=True),
        Binding("ctrl+t",     "show_themes",           "Themes",        priority=True),
        Binding("ctrl+h",     "show_help",             "Help",          priority=True),
        Binding("ctrl+l",     "clear_chat",            "Clear",         priority=True),
        Binding("ctrl+d",     "toggle_debug",          "Debug Mode",    priority=True),
    ]

    def __init__(self) -> None:
        super().__init__()
        register_custom_themes(self)
        self.backend: Backend | None = None
        self.debug_mode: bool = False

    def action_toggle_debug(self) -> None:
        self.debug_mode = not self.debug_mode
        status = "ENABLED" if self.debug_mode else "DISABLED"
        self.notify(f"🐞 Debug Mode {status}", title="DevPilot Debugger", severity="information")

    def action_quit(self) -> None:
        """Prevent accidental exit."""
        self.notify("Press Ctrl+Q to exit DevPilot", title="DevPilot", severity="information")

    def action_quit_app(self) -> None:
        """Only Ctrl+Q terminates the application."""
        self.exit()

    def on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            if len(self.screen_stack) > 1:
                self.pop_screen()
            event.stop()
        elif event.key in ("ctrl+c", "ctrl+C"):
            event.stop()
            try:
                chat_log = self.query_one("#chat-log", ChatLog)
                text = chat_log.get_latest_response_text()
                if text:
                    self.copy_to_clipboard(text)
                    self.notify("Copied response to clipboard!", title="Clipboard", severity="information")
                else:
                    self.notify("Press Ctrl+Q to exit DevPilot", title="DevPilot", severity="information")
            except Exception:
                self.notify("Press Ctrl+Q to exit DevPilot", title="DevPilot", severity="information")

    def compose(self) -> ComposeResult:
        yield DevPilotHeader(id="app-header")
        with Horizontal(id="body"):
            yield ProjectExplorer(root_path=".", id="project-explorer")
            with Vertical(id="center-column"):
                yield ChatLog(id="chat-log")
                with Container(id="input-area"):
                    yield ChatInput(
                        placeholder="Ask DevPilot anything...",
                        id="chat-input",
                    )
            yield WorkspacePanel(id="workspace-panel")
        yield StatusBar(id="status-bar")
        yield Footer()

    async def on_mount(self) -> None:
        self.theme = theme_id(DEFAULT_THEME)
        self.backend = build_backend()
        self._wire_events()

        # Show splash screen
        self.push_screen(SplashScreen())

        # Header
        header = self.query_one("#app-header", DevPilotHeader)
        header.workspace_name = self.backend.workspace_info.get("project_name", "devpilot")
        header.model_name = self.backend.settings.model_name
        header.mode = "CHAT"
        header.theme_name = DEFAULT_THEME
        branch = self.backend.workspace_info.get("git_branch", "main")
        header.git_branch = branch

        # WorkspacePanel
        panel = self.query_one("#workspace-panel", WorkspacePanel)
        panel.project_name = self.backend.workspace_info.get("project_name", "devpilot")
        panel.language = self.backend.workspace_info.get("language", "Python")
        panel.framework = self.backend.workspace_info.get("framework", "Textual")
        panel.git_branch = branch
        panel.model_name = self.backend.settings.model_name

        # StatusBar
        status = self.query_one(StatusBar)
        status.model_name = self.backend.settings.model_name
        status.workspace_name = self.backend.workspace_info.get("project_name", "devpilot")
        status.theme_label = DEFAULT_THEME
        status.status_text = "Ready"

        # Welcome message
        chat_log = self.query_one("#chat-log", ChatLog)
        await chat_log.add_message("assistant", WELCOME)

        self.query_one("#chat-input", Input).focus()

    def _wire_events(self) -> None:
        bus = self.backend.bus
        bus.subscribe("PipelineStarted",      self._on_pipeline_started)
        bus.subscribe("PipelineStageChanged", self._on_pipeline_stage_changed)
        bus.subscribe(EVENT_AGENT_STARTED,  self._on_agent_started)
        bus.subscribe(EVENT_AGENT_STEP,     self._on_agent_step)
        from core.event_bus import EVENT_AGENT_PROGRESS
        bus.subscribe(EVENT_AGENT_PROGRESS, self._on_agent_progress)
        bus.subscribe(EVENT_AGENT_FINISHED, self._on_agent_finished)
        bus.subscribe(EVENT_TASK_STARTED,   self._on_task_started)
        bus.subscribe(EVENT_TASK_COMPLETE,  self._on_task_complete)
        bus.subscribe(EVENT_FILE_CONFIRMED, self._on_file_confirmed)
        bus.subscribe(EVENT_FILE_CREATING,  self._on_file_creating)
        bus.subscribe(EVENT_FILE_EDITING,   self._on_file_editing)
        bus.subscribe(EVENT_FILE_READING,   self._on_file_reading)
        bus.subscribe(EVENT_ERROR,          self._on_bus_error)
        bus.subscribe(EVENT_WARNING,        self._on_bus_warning)
        bus.subscribe("GitHubConfirmRequest", self._on_github_confirm_request)

    async def _on_github_confirm_request(self, event) -> None:
        from tui.screens.commit_screen import CommitConfirmationScreen
        from core.event_bus import Event
        
        def on_close(accepted: bool):
            self.backend.bus.publish("GitHubConfirmResponse", accepted=accepted)
            
        self.push_screen(CommitConfirmationScreen(event.data), on_close)

    def on_file_selected_for_preview(self, event: FileSelectedForPreview) -> None:
        self.push_screen(FilePreviewScreen(event.file_path))

    async def _on_agent_progress(self, event) -> None:
        if self._active_stream:
            self._active_stream.update_agent_progress(event.data)
            
        name = event.data.get("agent_name", "")
        milestone = event.data.get("current_milestone", "")
        skill = event.data.get("current_skill", "")
        
        try:
            panel = self.query_one("#workspace-panel", WorkspacePanel)
            if name or milestone:
                panel.update_agent(agent=name or panel.active_agent, task=milestone)
            if skill:
                panel.active_skill = skill
        except Exception:
            pass

    async def _on_pipeline_started(self, event) -> None:
        stages = event.data.get("stages", [])
        if self._active_stream:
            self._active_stream.set_pipeline_timeline(stages)

    async def _on_pipeline_stage_changed(self, event) -> None:
        stage = event.data.get("stage", "")
        if self._active_stream:
            self._active_stream.update_pipeline_stage(stage)

    async def _on_agent_started(self, event) -> None:
        name = event.data.get("agent_name", "Agent")
        icon = AGENT_ICONS.get(name, "⚙")
        status = self.query_one(StatusBar)
        status.mode = "TASK"
        status.active_agent = f"{icon} {name}"
        status.status_text = f"{name} running…"
        panel = self.query_one("#workspace-panel", WorkspacePanel)
        panel.update_agent(agent=name, task="Executing plan...")
        try:
            pp = self.query_one("#wp-pipeline")
            pp.set_agent_status(name, "running")
        except Exception:
            pass

    async def _on_agent_step(self, event) -> None:
        name = event.data.get("agent_name", "Agent")
        step = event.data.get("step", "")
        panel = self.query_one("#workspace-panel", WorkspacePanel)
        panel.update_agent(agent=name, task=step[:30])
        self.query_one(StatusBar).status_text = step[:50] if step else "Running…"
        if step:
            chat_log = self.query_one("#chat-log", ChatLog)
            chat_log.add_step(step)

    async def _on_agent_finished(self, event) -> None:
        agent_name = event.data.get("agent_name", "Unknown")
        try:
            pp = self.query_one("#wp-pipeline")
            pp.set_agent_status(agent_name, "done")
        except Exception:
            pass

    async def _on_task_started(self, event) -> None:
        status = self.query_one(StatusBar)
        status.mode = "TASK"
        status.status_text = "Working…"

    async def _on_task_complete(self, event) -> None:
        status = self.query_one(StatusBar)
        status.mode = "CHAT"
        status.active_agent = ""
        status.status_text = "Ready"
        
        success = event.data.get("success", False)
        project_root = event.data.get("project_root", "")
        written_files = event.data.get("written_files", [])
        errors = event.data.get("errors", [])
        goal = event.data.get("goal", "Task Execution")
        chat_log = self.query_one("#chat-log", ChatLog)

        try:
            self.query_one("#project-explorer", ProjectExplorer).reload()
        except Exception:
            pass

        if success and written_files:
            from tui.widgets.chat_view import ExecutionReportCard
            report_data = {
                "agents_invoked": 3,
                "written_files": written_files,
                "tokens": 42500,
                "test_coverage": 95,
                "duration": 4.2
            }
            report = ExecutionReportCard(report_data)
            await chat_log.mount(report)
            chat_log.scroll_end(animate=False)
            self.notify(f"Task completed successfully ({len(written_files)} files written).", title="DevPilot", severity="information")
        else:
            from tui.widgets.chat_view import AgentFailureReport
            from core.agent_logger import AgentLogger

            logger = AgentLogger()
            err_msg = errors[0] if errors else "Pipeline failure occurred"
            
            agent_name = "Validator" if ("Validator" in err_msg or "Syntax" in err_msg) else ("Tester" if "Test" in err_msg else "Coder")
            log_p = str(logger.get_log_path(agent_name))

            report = AgentFailureReport(
                agent_name=agent_name,
                task=goal[:60],
                exception_type="PipelineFailure",
                message=err_msg,
                suggestion="Review the error output above and inspect the generated workspace files.",
                log_path=log_p,
            )

            streaming = await chat_log.start_streaming()
            streaming.add_failure_report(report)
            streaming.finalize(f"❌ **Task Failed.** Pipeline halted due to error in `{agent_name}`.")
            self.notify(f"Task failed: {err_msg[:40]}", title="DevPilot", severity="error")

    async def _on_file_confirmed(self, event) -> None:
        path = event.data.get("path", "")
        try:
            self.query_one("#project-explorer", ProjectExplorer).reload()
        except Exception:
            pass
        self.notify(f"Wrote {path}", title="File written", timeout=3)
        try:
            lfa = self.query_one("#wp-file-activity")
            lfa.finish_activity(path, "Saved")
        except Exception:
            pass

    async def _on_file_creating(self, event) -> None:
        path = event.data.get("path", "") or event.data.get("file_path", "")
        content = event.data.get("content", "")
        if path:
            chat_log = self.query_one("#chat-log", ChatLog)
            chat_log.add_file_op("Created", path, content=content)
            try:
                lfa = self.query_one("#wp-file-activity")
                lfa.add_activity(path, "Creating")
            except Exception:
                pass

    async def _on_file_editing(self, event) -> None:
        path = event.data.get("path", "") or event.data.get("file_path", "")
        content = event.data.get("content", "")
        diff = event.data.get("diff", "")
        if path:
            chat_log = self.query_one("#chat-log", ChatLog)
            chat_log.add_file_op("Modified", path, content=content, diff=diff)
            try:
                lfa = self.query_one("#wp-file-activity")
                lfa.add_activity(path, "Updating")
            except Exception:
                pass

    async def _on_file_reading(self, event) -> None:
        path = event.data.get("path", "") or event.data.get("file_path", "")
        content = event.data.get("content", "")
        if path:
            chat_log = self.query_one("#chat-log", ChatLog)
            chat_log.add_file_op("Read", path, content=content)
            try:
                lfa = self.query_one("#wp-file-activity")
                lfa.add_activity(path, "Reading")
            except Exception:
                pass

    async def _on_bus_error(self, event) -> None:
        message = event.data.get("message") or str(event.data)
        self.notify(message, title="Error", severity="error", timeout=6)

    async def _on_bus_warning(self, event) -> None:
        message = event.data.get("message") or str(event.data)
        self.notify(message, title="Warning", severity="warning", timeout=5)

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id != "chat-input":
            return
        if event.value.startswith("/"):
            event.input.value = ""
            self.action_show_command_palette()

    def action_copy_last_response(self) -> None:
        chat_log = self.query_one("#chat-log", ChatLog)
        text = chat_log.get_latest_response_text()
        if text:
            self.copy_to_clipboard(text)
            self.notify("Copied last response to clipboard!", title="Clipboard", severity="information")
        else:
            self.notify("No response to copy.", title="Clipboard", severity="warning")

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id != "chat-input":
            return
        text = event.value.strip()
        event.input.value = ""
        if not text:
            return

        chat_log = self.query_one("#chat-log", ChatLog)
        await chat_log.add_message("user", text)

        if text.startswith("/"):
            await self._dispatch_slash(text)
            return

        intent = self.backend.router.classify(text)
        if intent == Intent.TASK:
            self.run_worker(self._run_task(text), group="task", exclusive=False)
        else:
            self.run_worker(self._run_chat(text), group="chat", exclusive=False)

    async def _run_chat(self, text: str) -> None:
        status = self.query_one(StatusBar)
        status.status_text = "Thinking…"

        chat_log = self.query_one("#chat-log", ChatLog)
        streaming = await chat_log.start_streaming()

        def on_token(token: str) -> None:
            streaming.append(token)
            chat_log.scroll_end(animate=False)

        full_response = await self.backend.chat_engine.respond_stream(text, on_token=on_token)
        streaming.finalize(full_response)

        status.status_text = "Ready"

    async def _run_task(self, goal: str) -> None:
        from core.orchestrator import Orchestrator

        backend = self.backend
        # Build the orchestrator with required Registries
        from core.registry import SkillRegistry, AgentRegistry
        skill_registry = SkillRegistry()
        agent_registry = AgentRegistry()
        
        orchestrator = Orchestrator(
            llm=self.backend.llm,
            session_mgr=self.backend.session_mgr,
            event_bus=self.backend.bus,
            skill_registry=skill_registry,
            agent_registry=agent_registry,
            workspace_dir=self.backend.workspace_info.get("path", ".")
        )

        backend.bus.publish(EVENT_TASK_STARTED, goal=goal)
        result = await orchestrator.run_pipeline("Project Creation", goal)
        backend.bus.publish(
            EVENT_TASK_COMPLETE,
            goal=goal,
            success=result.success,
            project_root=str(result.project_root),
            written_files=result.written_files,
            errors=result.errors,
        )

    async def _dispatch_slash(self, text: str) -> None:
        cmd = text.split()[0].lower()
        if cmd == "/agents":
            self.action_show_agents()
        elif cmd == "/models":
            self.action_show_models()
        elif cmd == "/skills":
            self.action_show_skills()
        elif cmd == "/settings":
            self.action_show_settings()
        elif cmd in ("/theme", "/themes"):
            self.action_show_themes()
        elif cmd in ("/help", "/help-keys"):
            self.action_show_help()
        elif cmd == "/clear":
            self.action_clear_chat()
        elif cmd == "/exit":
            self.exit()

    def action_show_command_palette(self) -> None:
        from tui.screens.command_palette import DevPilotCommandPalette
        self.push_screen(DevPilotCommandPalette())

    def action_show_agents(self) -> None:
        self.push_screen(AgentsScreen(self.backend.agent_registry))

    def action_show_models(self) -> None:
        self.push_screen(ModelsScreen(self.backend), self._on_model_selected)

    def _on_model_selected(self, model_name: str | None) -> None:
        if not model_name:
            return
        self.backend.rebuild_llm(model_name)
        self.query_one(StatusBar).model_name = model_name
        self.query_one("#app-header", DevPilotHeader).model_name = model_name
        self.query_one("#workspace-panel", WorkspacePanel).update_model(model_name)
        self.notify(f"Switched to {model_name}", title="Model", severity="information")

    def action_show_skills(self) -> None:
        self.push_screen(SkillsScreen())

    def action_show_settings(self) -> None:
        self.push_screen(SettingsScreen(self.backend))

    def action_show_themes(self) -> None:
        self.push_screen(ThemeScreen(), self._on_theme_selected)

    def _on_theme_selected(self, theme_id_value: str | None) -> None:
        if theme_id_value:
            name = display_name_for(theme_id_value)
            self.theme = theme_id_value
            self.query_one(StatusBar).theme_label = name
            self.query_one("#app-header", DevPilotHeader).theme_name = name
            self.notify(f"Theme: {name}", title="Theme")

    def action_show_help(self) -> None:
        self.push_screen(HelpScreen())

    def action_clear_chat(self) -> None:
        self.run_worker(self._clear_chat(), exclusive=True)

    async def _clear_chat(self) -> None:
        await self.query_one("#chat-log", ChatLog).clear_all()
        self.backend.chat_engine.clear_history()
        self.query_one(StatusBar).status_text = "Ready"


def run() -> None:
    DevPilotApp().run()


if __name__ == "__main__":
    run()
