from __future__ import annotations
from typing import Callable, Any

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Static, Markdown, Input

from core.event_bus import ApprovalRequest, ApprovalAction


class ApprovalScreen(ModalScreen[tuple[str, str]]):
    """Generic modal screen for all human approvals."""

    DEFAULT_CSS = """
    ApprovalScreen {
        align: center middle;
        background: rgba(0, 0, 0, 0.8);
    }
    
    #appr-container {
        width: 80;
        height: auto;
        max-height: 40;
        background: #090909;
        border: solid #3B82F6;
        padding: 1 2;
    }
    
    .appr-title {
        color: #3B82F6;
        text-style: bold;
        margin-bottom: 1;
        border-bottom: solid #2C2C2C;
        padding-bottom: 1;
    }
    
    .appr-subtitle {
        color: #A5A5A5;
        margin-bottom: 1;
    }

    #appr-details {
        background: #111111;
        border: solid #2C2C2C;
        padding: 1;
        margin-bottom: 1;
        max-height: 15;
        overflow-y: auto;
    }

    #appr-feedback {
        display: none;
        margin-bottom: 1;
    }

    #appr-feedback.-visible {
        display: block;
    }

    .appr-buttons {
        height: 3;
        align: right middle;
    }
    
    .appr-btn {
        margin-left: 1;
    }
    """

    def __init__(self, request: ApprovalRequest) -> None:
        self.request = request
        self._editing = False
        super().__init__()

    def compose(self) -> ComposeResult:
        with Container(id="appr-container"):
            yield Static(self.request.title, classes="appr-title")
            
            if self.request.message:
                yield Static(self.request.message, classes="appr-subtitle")
            
            if self.request.details:
                with VerticalScroll(id="appr-details"):
                    yield Markdown(self.request.details)
            
            yield Input(placeholder="Enter feedback (e.g., 'Use PostgreSQL instead of SQLite')...", id="appr-feedback")

            with Horizontal(classes="appr-buttons", id="appr-buttons-row"):
                for action in self.request.actions:
                    yield Button(action.label, variant=action.variant, id=f"btn-{action.id}", classes="appr-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        action_id = event.button.id.replace("btn-", "") if event.button.id else ""
        
        # If edit was clicked, and we aren't showing the input yet, show it
        if action_id == "edit" and not self._editing:
            self._editing = True
            feedback_input = self.query_one("#appr-feedback", Input)
            feedback_input.add_class("-visible")
            feedback_input.focus()
            
            # Change the button to say "Submit Feedback"
            event.button.label = "Submit Feedback"
            return
            
        feedback_val = ""
        if self._editing:
            feedback_val = self.query_one("#appr-feedback", Input).value.strip()

        self.dismiss((action_id, feedback_val))
