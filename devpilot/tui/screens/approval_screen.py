"""
tui/screens/approval_screen.py
==============================
Human-in-the-Loop (HITL) Agent Approval Screen.
Displays an agent's proposed plan, architecture, or code in a TextArea
so the user can edit it before explicitly approving or rejecting it.
"""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label, TextArea


class AgentApprovalScreen(ModalScreen[str | None]):
    """Modal to review and optionally edit agent output before continuing."""

    DEFAULT_CSS = """
    AgentApprovalScreen {
        align: center middle;
        background: $background 80%;
    }

    #approval-container {
        width: 90%;
        height: 90%;
        background: #161B22;
        border: solid #30363D;
        padding: 1 2;
    }

    #approval-header {
        text-style: bold;
        color: #E6EDF3;
        margin-bottom: 1;
        text-align: center;
    }

    #approval-textarea {
        height: 1fr;
        border: solid #2F81F7;
        margin-bottom: 1;
        background: #0D1117;
        color: #E6EDF3;
    }

    #approval-buttons {
        height: 3;
        align: center middle;
    }

    #btn-approve {
        background: #238636;
        color: white;
        margin-right: 2;
        border: none;
    }

    #btn-approve:hover {
        background: #2EA043;
    }

    #btn-reject {
        background: #DA3633;
        color: white;
        border: none;
    }

    #btn-reject:hover {
        background: #F85149;
    }
    """

    def __init__(self, agent_name: str, task_desc: str, initial_content: str, language: str = "json") -> None:
        super().__init__()
        self.agent_name = agent_name
        self.task_desc = task_desc
        self.initial_content = initial_content
        self.language = language

    def compose(self) -> ComposeResult:
        with Vertical(id="approval-container"):
            yield Label(f"{self.agent_name.capitalize()} Request: {self.task_desc}", id="approval-header")
            
            text_area = TextArea(self.initial_content, id="approval-textarea", language=self.language)
            yield text_area
            
            with Horizontal(id="approval-buttons"):
                yield Button("✓ Approve & Continue", id="btn-approve")
                yield Button("✗ Reject", id="btn-reject")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-approve":
            text_area = self.query_one("#approval-textarea", TextArea)
            self.dismiss(text_area.text)
        elif event.button.id == "btn-reject":
            self.dismiss(None)
