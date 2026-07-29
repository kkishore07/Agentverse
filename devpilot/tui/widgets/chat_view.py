"""
tui/widgets/chat_view.py
=========================
Continuous AI Document Flow with Live Code Streaming & Expandable File Cards.
- Live Code Streaming: Generated code is displayed line-by-line inline.
- Expandable File Cards: Displays status, language, preview & diff for created/edited files.
- Document Flow: Pure ChatGPT/Claude style, zero Slack clutter.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.reactive import reactive
from textual.widgets import Button, Collapsible, Markdown, Static

RoleType = Literal["user", "assistant", "system", "error"]


@dataclass
class AgentFailureReport:
    agent_name: str
    task: str
    exception_type: str
    message: str
    stack_trace: str = ""
    affected_file: str = ""
    affected_line: Optional[int] = None
    command_executed: str = ""
    exit_code: Optional[int] = None
    stdout: str = ""
    stderr: str = ""
    suggestion: str = ""
    log_path: str = ""


class FailureReportCard(Vertical):
    """Detailed Agent Failure Report Card with command output and suggested fix."""

    DEFAULT_CSS = """
    FailureReportCard {
        height: auto;
        margin: 1 0;
        padding: 1 2;
        background: #1A0A0A;
        border-left: thick #F85149;
        border: solid #30363D;
    }

    .frc-header {
        color: #F85149;
        text-style: bold;
        margin-bottom: 1;
        height: 2;
    }

    .frc-detail {
        color: #E6EDF3;
        margin-bottom: 1;
    }

    .frc-suggestion {
        color: #56D364;
        text-style: bold;
        margin-top: 1;
    }
    """

    def __init__(self, report: AgentFailureReport) -> None:
        self.report = report
        super().__init__()

    def compose(self) -> ComposeResult:
        r = self.report
        yield Static(f"✗  {r.agent_name.capitalize()} Agent Failed", classes="frc-header")
        yield Static(f"[#7D8590]Task:[/] [bold #E6EDF3]{r.task}[/]", classes="frc-detail")

        if r.command_executed:
            yield Static(f"[#7D8590]Command:[/] [bold #2F81F7]{r.command_executed}[/]  (Exit: [bold #F85149]{r.exit_code if r.exit_code is not None else 'N/A'}[/])", classes="frc-detail")

        if r.affected_file:
            loc_str = f"{r.affected_file}" + (f":{r.affected_line}" if r.affected_line else "")
            yield Static(f"[#7D8590]Location:[/] [bold #E3B341]{loc_str}[/]", classes="frc-detail")

        yield Static(f"[bold #F85149][{r.exception_type}][/] {r.message}", classes="frc-detail")

        if r.stdout or r.stderr:
            out_content = (r.stdout + ("\n" + r.stderr if r.stderr else "")).strip()
            with Collapsible(title="▾ View Output & Traceback", collapsed=False):
                yield Markdown(f"```text\n{out_content}\n```")

        if r.suggestion:
            yield Static(f"💡 [bold #56D364]Suggested Fix:[/] {r.suggestion}", classes="frc-suggestion")

        if r.log_path:
            yield Static(f"[dim #7D8590]Log: {r.log_path}[/]", classes="frc-detail")


# ---------------------------------------------------------------------------
# ExecutionReportCard
# ---------------------------------------------------------------------------
class ExecutionReportCard(Vertical):
    """Professional execution report rendered after a pipeline run."""
    DEFAULT_CSS = """
    ExecutionReportCard {
        height: auto;
        margin: 1 0;
        padding: 1 2;
        background: #0A1A0F;
        border-left: thick #56D364;
        border: solid #30363D;
    }
    .erc-title {
        color: #56D364;
        text-style: bold;
        margin-bottom: 1;
        height: 2;
    }
    .erc-row { layout: horizontal; height: 1; }
    .erc-key { color: #7D8590; width: 20; }
    .erc-val { color: #E6EDF3; text-style: bold; width: 1fr; }
    """

    def __init__(self, data: dict) -> None:
        self.data = data
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Static("✓  PIPELINE EXECUTION COMPLETE", classes="erc-title")

        stats = [
            ("Agents Invoked",  str(self.data.get("agents_invoked", 0))),
            ("Files Written",   str(len(self.data.get("written_files", [])))),
            ("Tokens Consumed", f"{self.data.get('tokens', 0):,}"),
            ("Test Coverage",   f"{self.data.get('test_coverage', 0)}%"),
            ("Duration",        f"{self.data.get('duration', 0.0):.1f}s"),
        ]

        for k, v in stats:
            with Horizontal(classes="erc-row"):
                yield Static(f"{k}:", classes="erc-key")
                yield Static(v, classes="erc-val")

# ---------------------------------------------------------------------------
# ExpandableFileCard (Live File & Diff Preview)
# ---------------------------------------------------------------------------

from rich.text import Text

class ExpandableFileCard(Vertical):
    """Expandable File Card displaying status, language, code preview & diffs."""

    DEFAULT_CSS = """
    ExpandableFileCard {
        height: auto;
        margin: 1 0;
        padding: 0;
        background: $surface;
        border-left: thick $primary;
        border: solid $panel;
    }

    .fc-header {
        color: $foreground;
        text-style: bold;
        padding: 0 1;
        height: 2;
        background: $panel;
        align: left middle;
    }

    .fc-header-created  { border-left: thick $success; }
    .fc-header-modified { border-left: thick $warning; }
    .fc-header-read     { border-left: thick $primary; }

    .fc-status-create { color: $success; }
    .fc-status-edit   { color: $warning; }
    .fc-status-read   { color: $primary; }

    ExpandableFileCard Collapsible {
        background: transparent;
        border: none;
        padding: 0 1 1 1;
    }

    .diff-viewer {
        background: $background;
        padding: 1;
        border: solid $panel;
    }
    """

    def __init__(self, op: str, path: str, content: str = "", diff: str = "") -> None:
        self.op = op
        self.path = path
        self.content = content
        self.diff = diff
        super().__init__()

    def _render_diff(self) -> Text:
        lines = self.diff.splitlines()
        text = Text()
        for line in lines:
            if line.startswith("+"):
                text.append(line + "\n", style="bold #56D364 on #0A1A0F")
            elif line.startswith("-"):
                text.append(line + "\n", style="bold #F85149 on #1A0A0A")
            elif line.startswith("@@"):
                text.append(line + "\n", style="bold #58A6FF")
            else:
                text.append(line + "\n", style="#7D8590")
        return text

    def compose(self) -> ComposeResult:
        ext = self.path.split(".")[-1] if "." in self.path else "text"
        status_key = "create" if self.op.lower() in ("create", "created") else ("edit" if self.op.lower() in ("edit", "modified") else "read")

        op_icon = "+" if status_key == "create" else ("✏" if status_key == "edit" else "👁")
        op_color = "#56D364" if status_key == "create" else ("#E3B341" if status_key == "edit" else "#2F81F7")

        yield Static(
            f"[{op_color}]{op_icon}[/]  {self.path}  [dim #7D8590]· {ext.upper()}[/]",
            classes=f"fc-header fc-status-{status_key}",
        )

        title = "▾ Code Diff" if self.diff else "▾ Code Preview"
        with Collapsible(title=title, collapsed=False):
            if self.diff:
                yield Static(self._render_diff(), classes="diff-viewer")
            elif self.content:
                yield Markdown(f"```{ext}\n{self.content}\n```")
            else:
                yield Static(f"[dim #7D8590]File {self.op.lower()} at {self.path}[/]")

# ---------------------------------------------------------------------------
# ChatMessage (User, System, Error)
# ---------------------------------------------------------------------------

class ChatMessage(Vertical):
    """Clean document message block for User, System, or Error."""

    DEFAULT_CSS = """
    ChatMessage {
        height: auto;
        margin: 0 0 1 0;
        padding: 0;
    }

    ChatMessage.-user {
        background: $boost;
        color: $foreground;
        width: 1fr;
        margin: 0 0 1 0;
        padding: 1 2;
        border-left: thick $primary;
    }

    ChatMessage.-system {
        background: transparent;
        color: $foreground 50%;
        padding: 0;
    }

    ChatMessage.-error {
        background: #1A0A0A;
        border-left: thick $error;
        color: $error;
        padding: 1 2;
        margin-bottom: 1;
    }

    .msg-role-user {
        color: $primary;
        text-style: bold;
        height: 1;
        margin-bottom: 1;
    }

    .msg-role-sys {
        display: none;
    }

    ChatMessage Markdown {
        background: transparent;
        margin: 0;
        padding: 0;
    }
    """

    def __init__(self, role: str, content: str) -> None:
        self._role = role
        self._content = content
        super().__init__(classes=f"chat-message -{role}")

    def compose(self) -> ComposeResult:
        if self._role == "user":
            yield Static("👤  You", classes="msg-role-user")
        else:
            yield Static("⚙ System", classes="msg-role-sys")

        yield Markdown(self._content)


# ---------------------------------------------------------------------------
# AgentProgressCard (Live Agent Grid)
# ---------------------------------------------------------------------------

from textual.widgets import ProgressBar

class AgentProgressCard(Static):
    """Inline minimalist thinking indicator."""

    DEFAULT_CSS = """
    AgentProgressCard {
        color: $foreground 50%;
        height: 1;
        margin-bottom: 1;
    }
    """

    def __init__(self) -> None:
        super().__init__("⠋  Thinking...")
        self.hidden = False

    def update_data(self, data: dict) -> None:
        if "llm_token" in data and not self.hidden:
            self.display = False
            self.hidden = True
            return

        step = data.get("step") or data.get("operation")
        if step and not self.hidden:
            self.update(f"⠋  {step}...")


# ---------------------------------------------------------------------------
# StreamingMessage (Assistant Continuous Response)
# ---------------------------------------------------------------------------

class StreamingMessage(Vertical):
    """Continuous Assistant Document Flow owning Thinking, File Cards & Streamed Code/Markdown."""

    DEFAULT_CSS = """
    StreamingMessage {
        height: auto;
        margin: 0 0 2 0;
        padding: 0;
        background: transparent;
        border: none;
    }

    .asst-header-row {
        height: 2;
        margin-bottom: 1;
        background: $panel;
        align: left middle;
        padding: 0 1;
    }

    #timeline-container {
        display: none;
    }

    .msg-role-asst {
        color: $primary;
        text-style: bold;
        width: 1fr;
    }

    .asst-copy-btn {
        height: 1;
        min-width: 16;
        border: none;
        background: transparent;
        color: $foreground 40%;
        padding: 0 1;
    }

    .asst-copy-btn:hover {
        background: $boost;
        color: $foreground;
    }

    #thinking-container {
        height: auto;
        background: transparent;
        padding: 0 1;
    }

    .step-line {
        color: $foreground 50%;
        height: 1;
    }

    #file-ops-container {
        height: auto;
        margin-bottom: 1;
        background: transparent;
    }

    StreamingMessage Markdown {
        background: transparent;
        margin: 0;
        padding: 0 1;
    }

    StreamingMessage MarkdownFence {
        background: $panel;
        border: solid $boost;
        margin: 1 0;
    }

    .streaming-cursor {
        color: $primary;
        height: 1;
        padding: 0 1;
    }

    .timeline-stage {
        color: $foreground 40%;
        padding: 0 1;
        height: 1;
        border: solid $panel;
        margin-right: 1;
    }

    .active-stage {
        color: $primary;
        text-style: bold;
        border: solid $primary;
    }

    .timeline-arrow {
        color: $foreground 30%;
        height: 1;
        width: 3;
        align: center middle;
    }
    """

    text: reactive[str] = reactive("", always_update=True)

    def __init__(self) -> None:
        super().__init__(classes="streaming-message -assistant")
        self._buffer = ""
        self._seen_file_ops: dict[str, ExpandableFileCard] = {}

    def compose(self) -> ComposeResult:
        with Horizontal(classes="asst-header-row"):
            yield Static("◈  AgentVerse", classes="msg-role-asst")
            yield Button("📋 Copy", id="btn-copy-asst", classes="asst-copy-btn")
        yield Horizontal(id="timeline-container", classes="timeline-hidden")
        yield Vertical(id="thinking-container")
        yield Vertical(id="file-ops-container")
        yield Markdown("", id="stream-body")
        yield Static("▍", classes="streaming-cursor", id="stream-cursor")

    def get_full_response_text(self) -> str:
        """Aggregate the full response text including Markdown response and all generated code blocks."""
        parts = []
        if self._buffer:
            parts.append(self._buffer)

        if self._seen_file_ops:
            parts.append("\n\n### Generated Implementation:\n")
            for card_key, card in self._seen_file_ops.items():
                ext = card.path.split(".")[-1] if "." in card.path else "text"
                if card.content:
                    parts.append(f"📄 **{card.path}**:\n```{ext}\n{card.content}\n```\n")
                elif card.diff:
                    parts.append(f"📄 **{card.path} (Diff)**:\n```diff\n{card.diff}\n```\n")

        return "\n".join(parts).strip()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-copy-asst":
            event.stop()
            full_text = self.get_full_response_text()
            if full_text:
                self.app.copy_to_clipboard(full_text)
                self.app.notify("Copied response & code to clipboard!", title="Clipboard", severity="information")

    def add_step(self, step_text: str) -> None:
        """Add an inline step under Thinking."""
        try:
            container = self.query_one("#thinking-container", Vertical)
            container.mount(Static(f"  ✓ {step_text}", classes="step-line"))
        except Exception:
            pass

    def add_file_op(self, op: str, path: str, content: str = "", diff: str = "") -> None:
        """Add or update an inline expandable file card (deduplicated by path)."""
        try:
            container = self.query_one("#file-ops-container", Vertical)
            card_key = f"{op}:{path}"
            if card_key in self._seen_file_ops:
                card = self._seen_file_ops[card_key]
                if content:
                    card.content = content
                if diff:
                    card.diff = diff
            else:
                card = ExpandableFileCard(op, path, content, diff)
                self._seen_file_ops[card_key] = card
                container.mount(card)
        except Exception:
            pass

    def add_failure_report(self, report: AgentFailureReport) -> None:
        """Mount an Agent Failure Report Card into the streaming document flow."""
        try:
            container = self.query_one("#file-ops-container", Vertical)
            container.mount(FailureReportCard(report))
        except Exception:
            pass

    def set_pipeline_timeline(self, stages: list[str]) -> None:
        """Set up the timeline UI for the pipeline stages."""
        try:
            container = self.query_one("#timeline-container", Horizontal)
            container.remove_class("timeline-hidden")
            container.query("*").remove()
            for idx, stage in enumerate(stages):
                label = Static(f"{stage.capitalize()}", id=f"stage-{stage}", classes="timeline-stage")
                container.mount(label)
                if idx < len(stages) - 1:
                    container.mount(Static("→", classes="timeline-arrow"))
        except Exception:
            pass

    def update_pipeline_stage(self, stage: str) -> None:
        """Highlight the active pipeline stage."""
        try:
            container = self.query_one("#timeline-container", Horizontal)
            for widget in container.query(".timeline-stage"):
                if widget.id == f"stage-{stage}":
                    widget.add_class("active-stage")
                else:
                    widget.remove_class("active-stage")
        except Exception:
            pass

    def update_agent_progress(self, data: dict) -> None:
        """Dynamically update agent progress fields and route llm tokens to text buffer."""
        agent_name = data.get("agent_name", "agent")

        # Handle streaming LLM tokens
        if "llm_token" in data:
            self.append(data["llm_token"])

        # Mount or update the AgentProgressCard
        try:
            container = self.query_one("#thinking-container", Vertical)
            card_id = f"apc-{agent_name}"

            matches = container.query(f"#{card_id}")
            if matches:
                card = matches.first()
            else:
                card = AgentProgressCard()
                card.id = card_id
                container.mount(card)

            card.update_data(data)
        except Exception:
            pass

    def append(self, token: str) -> None:
        self._buffer += token
        self.text = self._buffer

    def watch_text(self, value: str) -> None:
        try:
            self.query_one("#stream-body", Markdown).update(value or "▍")
        except Exception:
            pass

    def finalize(self, full_text: str = "") -> None:
        if full_text:
            self._buffer = full_text
            self.text = full_text
        try:
            self.query_one("#stream-cursor", Static).display = False
        except Exception:
            pass


# ---------------------------------------------------------------------------
# ChatLog (Document Container)
# ---------------------------------------------------------------------------

class ChatLog(VerticalScroll):
    """Scrollable document canvas for continuous AI conversation & Live Code Implementation."""

    DEFAULT_CSS = """
    ChatLog {
        height: 1fr;
        padding: 1 3;
        background: $background;
        border: none;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._active_stream: StreamingMessage | None = None

    async def add_message(self, role: str, content: str) -> "ChatMessage | StreamingMessage":
        if role == "assistant":
            stream = StreamingMessage()
            await self.mount(stream)
            stream.finalize(content)
            self.scroll_end(animate=False)
            return stream

        widget = ChatMessage(role, content)
        await self.mount(widget)
        self.scroll_end(animate=False)
        return widget

    async def start_streaming(self) -> StreamingMessage:
        stream = StreamingMessage()
        self._active_stream = stream
        await self.mount(stream)
        self.scroll_end(animate=False)
        return stream

    def get_active_stream(self) -> StreamingMessage:
        if self._active_stream is None:
            stream = StreamingMessage()
            self._active_stream = stream
            self.mount(stream)
        return self._active_stream

    def add_step(self, step_text: str) -> None:
        stream = self.get_active_stream()
        stream.add_step(step_text)
        self.scroll_end(animate=False)

    def add_file_op(self, op: str, path: str, content: str = "", diff: str = "") -> None:
        stream = self.get_active_stream()
        stream.add_file_op(op, path, content, diff)
        self.scroll_end(animate=False)

    async def clear_all(self) -> None:
        self._active_stream = None
        await self.remove_children()

    def get_latest_response_text(self) -> str:
        """Retrieve plain text content of the latest AI assistant response including all code blocks."""
        for child in reversed(list(self.children)):
            if isinstance(child, StreamingMessage):
                full = child.get_full_response_text()
                if full:
                    return full
            elif isinstance(child, ChatMessage) and child._role != "user":
                return child._content
        return ""
