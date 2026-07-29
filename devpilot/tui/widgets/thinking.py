"""
tui/widgets/thinking.py
========================
Animated "thinking" timeline widget shown inside the chat log while
DevPilot is processing a request.

Design:
  🧠 Thinking...
    › Understanding request
    › Searching workspace
    › Planning response
    ✓ Done

Each step fades in sequentially. An animated progress dots cycle runs
on a timer until `finalize()` is called, then the panel either collapses
or shows a compact "done" state.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.reactive import reactive
from textual.timer import Timer
from textual.widget import Widget
from textual.widgets import Static


_DOT_FRAMES = ["   ", ".  ", ".. ", "..."]
_THINKING_STEPS = [
    "Understanding request",
    "Searching workspace",
    "Planning response",
]


class ThinkingIndicator(Widget):
    """Animated thinking timeline that streams steps as they happen."""

    DEFAULT_CSS = """
    ThinkingIndicator {
        height: auto;
        margin: 0 0 1 0;
        padding: 1 2;
        background: $surface;
        border-left: thick $warning;
        display: block;
    }

    ThinkingIndicator.-done {
        border-left: thick $success;
        opacity: 0.7;
    }

    ThinkingIndicator .think-header {
        color: $warning;
        text-style: bold;
        height: 1;
        margin-bottom: 1;
    }

    ThinkingIndicator.-done .think-header {
        color: $success;
    }

    ThinkingIndicator .think-step {
        color: $foreground 50%;
        height: 1;
        padding-left: 2;
    }

    ThinkingIndicator .think-step.-done {
        color: $success;
    }

    ThinkingIndicator .think-step.-active {
        color: $warning;
        text-style: bold;
    }

    ThinkingIndicator .think-dots {
        color: $warning;
        height: 1;
        padding-left: 2;
    }
    """

    _dot_idx: reactive[int] = reactive(0, init=False)
    _done: reactive[bool] = reactive(False, init=False)

    def __init__(self) -> None:
        super().__init__()
        self._steps_shown: list[str] = []
        self._timer: Timer | None = None
        self._dot_timer: Timer | None = None
        self._step_widgets: list[Static] = []

    def compose(self) -> ComposeResult:
        yield Static("🧠 Thinking", classes="think-header", id="think-hdr")
        yield Static("", classes="think-dots", id="think-dots")

    def on_mount(self) -> None:
        self._dot_timer = self.set_interval(0.35, self._tick_dots)

    def _tick_dots(self) -> None:
        self._dot_idx = (self._dot_idx + 1) % len(_DOT_FRAMES)
        try:
            dots_widget = self.query_one("#think-dots", Static)
            dots_widget.update(f"  {_DOT_FRAMES[self._dot_idx]}")
        except Exception:
            pass

    def add_step(self, step: str) -> None:
        """Add a visible step to the timeline."""
        widget = Static(f"  › {step}", classes="think-step -active")
        self._step_widgets.append(widget)
        self._steps_shown.append(step)
        self.mount(widget, before=self.query_one("#think-dots"))
        # Mark the previous step as done
        if len(self._step_widgets) > 1:
            prev = self._step_widgets[-2]
            prev.update(f"  ✓ {self._steps_shown[-2]}")
            prev.set_classes("think-step -done")

    def finalize(self, message: str = "Done") -> None:
        """Stop animation and mark all steps complete."""
        self._done = True
        if self._dot_timer:
            self._dot_timer.stop()
            self._dot_timer = None

        # Mark last step done
        if self._step_widgets:
            last_step = self._steps_shown[-1] if self._steps_shown else ""
            self._step_widgets[-1].update(f"  ✓ {last_step}")
            self._step_widgets[-1].set_classes("think-step -done")

        try:
            self.query_one("#think-hdr", Static).update(f"✓ {message}")
            self.query_one("#think-dots", Static).update("")
            self.add_class("-done")
        except Exception:
            pass

    def on_unmount(self) -> None:
        if self._dot_timer:
            self._dot_timer.stop()
