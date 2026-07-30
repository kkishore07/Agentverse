"""
tui/screens/models_screen.py
==============================
Scrollable Model Cards manager displaying all installed models and parameters.
"""

from __future__ import annotations

from dataclasses import dataclass
from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.message import Message
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Label, LoadingIndicator, Static

from tui.backend import Backend


@dataclass
class ModelInfo:
    id: str
    name: str
    provider: str
    context: str
    ram: str
    params: str
    quantization: str
    speed: str
    description: str


MOCK_METADATA = {
    "qwen2.5-coder": ModelInfo("qwen2.5-coder:3b", "Qwen 2.5 Coder (3B)", "Alibaba Cloud", "128K", "2.2 GB", "3B", "Q4_K_M", "*****", "State of the art lightweight code reasoning model."),
    "llama3": ModelInfo("llama3", "Llama 3 (8B)", "Meta", "8K", "4.7 GB", "8B", "Q4_0", "****", "Fast, capable general purpose model."),
    "llama3:70b": ModelInfo("llama3:70b", "Llama 3 (70B)", "Meta", "8K", "39 GB", "70B", "Q4_0", "**", "High quality, requires significant RAM."),
    "phi3": ModelInfo("phi3", "Phi-3 Mini", "Microsoft", "128K", "2.3 GB", "3.8B", "Q4_0", "*****", "Extremely fast, excellent reasoning."),
    "mistral": ModelInfo("mistral", "Mistral v0.2", "Mistral AI", "32K", "4.1 GB", "7B", "Q4_0", "****", "Solid performance and context window."),
    "mixtral": ModelInfo("mixtral", "Mixtral 8x7B", "Mistral AI", "32K", "26 GB", "47B", "Q4_0", "***", "MoE model with outstanding quality."),
    "codellama": ModelInfo("codellama", "Code Llama", "Meta", "16K", "4.7 GB", "7B", "Q4_0", "***", "Optimized for code generation."),
    "gemma": ModelInfo("gemma", "Gemma (7B)", "Google", "8K", "5.0 GB", "7B", "Q4_0", "***", "Google's open weight model."),
}


def get_model_info(model_id: str) -> ModelInfo:
    from dataclasses import replace
    for key, info in MOCK_METADATA.items():
        if key in model_id.lower():
            return replace(info, id=model_id)
    return ModelInfo(model_id, model_id.title(), "Local Ollama", "128K", "4GB+", "7B", "Q4_K_M", "****", "Local model running via Ollama service.")


class ModelSelected(Message):
    def __init__(self, model_id: str) -> None:
        self.model_id = model_id
        super().__init__()


class ModelCard(Container, can_focus=True):
    """Rich scrollable card displaying model metadata and selection controls."""

    DEFAULT_CSS = """
    ModelCard {
        height: 7;
        width: 100%;
        border: solid #2C2C2C;
        background: #171717;
        padding: 1 2;
        margin-bottom: 1;
    }

    ModelCard:focus {
        border: solid #3B82F6;
    }

    ModelCard.-current {
        border: heavy #10B981;
        background: #111111;
    }

    .mc-left {
        width: 1fr;
    }
    .mc-right {
        width: 22;
        align: right middle;
    }

    .mc-title {
        color: #ECECEC;
        text-style: bold;
        height: 1;
    }
    .mc-desc {
        color: #A5A5A5;
        height: 2;
    }
    .mc-stats {
        color: #3B82F6;
        height: 1;
    }
    .mc-btn {
        height: 1;
        border: none;
        background: #1F1F1F;
        color: #ECECEC;
    }
    .mc-btn:hover {
        background: #3B82F6;
        color: #FFFFFF;
    }
    """

    def __init__(self, info: ModelInfo, is_current: bool = False) -> None:
        import re
        self.info = info
        self.is_current = is_current
        self.safe_id = re.sub(r"[^a-zA-Z0-9_-]", "-", info.id)
        super().__init__(id=f"card-{self.safe_id}", classes="model-card" + (" -current" if is_current else ""))

    def compose(self) -> ComposeResult:
        with Horizontal():
            with Vertical(classes="mc-left"):
                status_tag = " [bold #10B981](Active)[/]" if self.is_current else ""
                yield Label(f"🧠 {self.info.name} [dim #A5A5A5]({self.info.provider})[/]{status_tag}", classes="mc-title")
                yield Label(self.info.description, classes="mc-desc")
                yield Label(f"Context: {self.info.context} | RAM: {self.info.ram} | Quant: {self.info.quantization} | Speed: {self.info.speed}", classes="mc-stats")

            with Vertical(classes="mc-right"):
                btn_label = "Active Model" if self.is_current else "Select Model"
                yield Button(btn_label, id=f"sel-{self.safe_id}", classes="mc-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.post_message(ModelSelected(self.info.id))

    def on_click(self) -> None:
        self.post_message(ModelSelected(self.info.id))

    def on_key(self, event) -> None:
        if event.key == "enter":
            self.post_message(ModelSelected(self.info.id))


class ModelsScreen(ModalScreen[str | None]):
    """Scrollable model manager screen."""

    BINDINGS = [Binding("escape", "dismiss_screen", "Close")]

    DEFAULT_CSS = """
    ModelsScreen {
        align: center middle;
        background: #090909 80%;
    }

    #models-container {
        width: 85%;
        height: 85%;
        border: solid #3B82F6;
        background: #111111;
        padding: 1 2;
    }

    .m-header {
        height: 3;
        border-bottom: solid #2C2C2C;
        margin-bottom: 1;
    }

    .m-title {
        text-style: bold;
        color: #3B82F6;
        width: 1fr;
    }

    #m-scroll {
        height: 1fr;
    }
    """

    def __init__(self, backend: Backend) -> None:
        self._backend = backend
        super().__init__()

    def compose(self) -> ComposeResult:
        with Container(id="models-container"):
            with Horizontal(classes="m-header"):
                yield Label(f"🧠 Installed LLM Providers & Models (Active: {self._backend.settings.model_name})", classes="m-title")
                yield Label("Esc Close", classes="m-hint")
            yield LoadingIndicator(id="m-loading")
            yield VerticalScroll(id="m-scroll")

    def on_mount(self) -> None:
        self._load_models()

    @work(exclusive=True)
    async def _load_models(self) -> None:
        models = await self._backend.llm.list_models()
        try:
            self.query_one("#m-loading", LoadingIndicator).display = False
        except Exception:
            pass

        scroll = self.query_one("#m-scroll", VerticalScroll)
        current = self._backend.settings.model_name
        names = models or [current, "llama3", "phi3", "mistral", "codellama", "gemma"]

        for name in names:
            info = get_model_info(name)
            is_current = name == current
            card = ModelCard(info, is_current=is_current)
            await scroll.mount(card)

    def on_model_selected(self, event: ModelSelected) -> None:
        event.stop()
        self.dismiss(event.model_id)

    def action_dismiss_screen(self) -> None:
        self.dismiss(None)

    def on_key(self, event) -> None:
        if event.key in ("escape", "q"):
            self.dismiss(None)
