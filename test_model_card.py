import re
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Static

class ModelInfo:
    def __init__(self, id, name, provider, context, ram, params, quantization, speed, description):
        self.id = id
        self.name = name
        self.provider = provider
        self.context = context
        self.ram = ram
        self.params = params
        self.quantization = quantization
        self.speed = speed
        self.description = description

class ModelCard(Container, can_focus=True):
    DEFAULT_CSS = """
    ModelCard {
        height: 7;
        border: solid red;
        padding: 1;
    }
    .mc-left { width: 1fr; }
    .mc-right { width: 25; text-align: right; }
    """
    def __init__(self, info: ModelInfo, is_current: bool = False) -> None:
        self.info = info
        self.is_current = is_current
        safe_id = re.sub(r"[^a-zA-Z0-9_-]", "-", info.id)
        super().__init__(id=f"card-{safe_id}", classes="model-card" + (" -current" if is_current else ""))

    def compose(self) -> ComposeResult:
        with Horizontal():
            with Vertical(classes="mc-left"):
                yield Static(f"◈ {self.info.name}", classes="mc-name")
                yield Static(self.info.description, classes="mc-desc")
                yield Static(f"[dim]Provider:[/dim] {self.info.provider}", classes="mc-prov")
            with Vertical(classes="mc-right"):
                yield Static(f"[dim]Ctx:[/dim] {self.info.context}  [dim]RAM:[/dim] {self.info.ram}", classes="mc-stats")
                yield Static(f"[dim]Prm:[/dim] {self.info.params}  [dim]Qnt:[/dim] {self.info.quantization}", classes="mc-stats")
                yield Static(f"[dim]Spd:[/dim] {self.info.speed}", classes="mc-stats")

class TestApp(App):
    def compose(self) -> ComposeResult:
        info = ModelInfo("test", "Test Model", "Local", "8K", "4GB", "7B", "Q4", "Fast", "A test model.")
        yield ModelCard(info)

if __name__ == "__main__":
    TestApp().run()
