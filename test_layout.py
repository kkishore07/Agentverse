from textual.app import App
from devpilot.tui.screens.models_screen import ModelCard, ModelInfo

class TestApp(App):
    CSS = """
    ModelCard {
        border: solid green;
    }
    """
    def compose(self):
        info = ModelInfo("test", "Test Model", "Local", "8K", "4GB", "7B", "Q4", "Fast", "A test model.")
        yield ModelCard(info)

if __name__ == "__main__":
    app = TestApp()
    app.run()
