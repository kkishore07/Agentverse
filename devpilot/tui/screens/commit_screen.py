from __future__ import annotations
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Static, Markdown

class CommitConfirmationScreen(ModalScreen[bool]):
    """Modal for confirming a GitHub commit."""

    DEFAULT_CSS = """
    CommitConfirmationScreen {
        align: center middle;
        background: rgba(0, 0, 0, 0.8);
    }
    
    #ccs-container {
        width: 80;
        height: auto;
        max-height: 40;
        background: #090909;
        border: solid #3B82F6;
        padding: 1 2;
    }
    
    .ccs-title {
        color: #3B82F6;
        text-style: bold;
        margin-bottom: 1;
        border-bottom: solid #2C2C2C;
        padding-bottom: 1;
    }
    
    .ccs-subtitle {
        color: #A5A5A5;
        margin-bottom: 1;
    }

    #ccs-message {
        background: #111111;
        border: solid #2C2C2C;
        padding: 1;
        margin-bottom: 1;
    }

    #ccs-diff {
        background: #111111;
        border: solid #2C2C2C;
        padding: 1;
        margin-bottom: 1;
        max-height: 15;
        overflow-y: auto;
    }

    .ccs-buttons {
        height: 3;
        align: right middle;
    }
    
    .ccs-btn-reject { margin-right: 2; background: #EF4444; color: white; border: none; }
    .ccs-btn-accept { background: #10B981; color: white; border: none; }
    """

    def __init__(self, data: dict) -> None:
        self.data = data
        super().__init__()

    def compose(self) -> ComposeResult:
        with Container(id="ccs-container"):
            yield Static("🌿 GITHUB COMMIT CONFIRMATION", classes="ccs-title")
            
            yield Static("The GitHub Agent generated the following commit message:", classes="ccs-subtitle")
            
            msg = self.data.get("message", "Update files")
            diff = self.data.get("diff", "No diff available")
            
            with VerticalScroll(id="ccs-message"):
                yield Markdown(f"```text\n{msg}\n```")
            
            yield Static("Diff Summary:", classes="ccs-subtitle")
            with VerticalScroll(id="ccs-diff"):
                yield Markdown(f"```text\n{diff}\n```")

            with Horizontal(classes="ccs-buttons"):
                yield Button("Reject", variant="error", id="btn-reject", classes="ccs-btn-reject")
                yield Button("Accept & Commit", variant="success", id="btn-accept", classes="ccs-btn-accept")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-accept":
            self.dismiss(True)
        elif event.button.id == "btn-reject":
            self.dismiss(False)
