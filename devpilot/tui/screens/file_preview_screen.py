"""
tui/screens/file_preview_screen.py
===================================
Syntax-highlighted file preview modal with metadata inspection.
"""

from __future__ import annotations

import os
from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Header, Label, Static, TextArea

class FilePreviewScreen(ModalScreen[None]):
    """Modal screen displaying file content with line numbers, syntax, and metadata."""

    DEFAULT_CSS = """
    FilePreviewScreen {
        align: center middle;
        background: #090909 80%;
    }

    #preview-container {
        width: 85%;
        height: 85%;
        border: solid #3B82F6;
        background: #111111;
        padding: 1;
    }

    #preview-header {
        height: 3;
        border-bottom: solid #2C2C2C;
        padding: 0 1;
    }

    .preview-title {
        text-style: bold;
        color: #3B82F6;
        width: 1fr;
    }

    .preview-meta {
        color: #A5A5A5;
    }

    #preview-content {
        height: 1fr;
        margin-top: 1;
    }

    #close-btn {
        width: 12;
        height: 1;
        border: none;
        background: #1F1F1F;
        color: #ECECEC;
    }
    #close-btn:hover {
        background: #3B82F6;
        color: #FFFFFF;
    }
    """

    def __init__(self, file_path: str) -> None:
        super().__init__()
        self.file_path = file_path

    def compose(self) -> ComposeResult:
        path = Path(self.file_path)
        size = "Unknown"
        ext = path.suffix or "Plain Text"
        try:
            stat = os.stat(self.file_path)
            size = f"{stat.st_size / 1024:.1f} KB"
        except Exception:
            pass

        content = ""
        try:
            with open(self.file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception as e:
            content = f"Error reading file: {e}"

        with Container(id="preview-container"):
            with Horizontal(id="preview-header"):
                yield Label(f"📄 {path.name}", classes="preview-title")
                yield Label(f"{ext} | {size}", classes="preview-meta")
                yield Button("Esc Close", id="close-btn")
            
            # Use TextArea for scrollable code viewing with line numbers
            text_area = TextArea(content, id="preview-content", read_only=True, show_line_numbers=True)
            yield text_area

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "close-btn":
            self.dismiss()

    def on_key(self, event) -> None:
        if event.key in ("escape", "q"):
            self.dismiss()
