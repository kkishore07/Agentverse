# DevPilot Textual TUI

**DevPilot** is an advanced, autonomous AI coding assistant running locally in your terminal. Built with Python and [Textual](https://textual.textualize.io/), DevPilot provides a rich Terminal User Interface (TUI) that feels like a modern code editor, giving you total transparency into the AI's autonomous execution pipeline.

![DevPilot Interface](https://via.placeholder.com/800x450.png?text=DevPilot+TUI+Screenshot) *(Example screenshot)*

---

## 🚀 Features

- **Rich Terminal UI**: A gorgeous, reactive, mouse-supported terminal interface with chat logs, file previews, and a dynamic workspace inspector.
- **Agentic Pipeline**: An autonomous team of specialized AI agents working together to fulfill your coding requests:
  - 🧠 **Planner Agent**: Analyzes your request and builds a step-by-step master plan.
  - 🏗️ **Architect Agent**: Determines the optimal file structure and dependencies.
  - 💻 **Coder Agent**: Streams and generates actual source code file-by-file.
  - 🔍 **Validator Agent**: Scans generated files for duplicate paths, syntax errors, and missing files.
  - 🧪 **Tester Agent**: Automatically runs your test suite (pytest, npm) and parses outcomes.
  - 🧐 **Reviewer Agent**: Performs static analysis for security, performance, and style issues.
  - 📖 **Documentation Agent**: Automatically authors and updates project `README.md`.
  - 🐙 **GitHub Agent**: Analyzes diffs, generates commit messages, and requests commit approval.
- **Real-Time Telemetry & EventBus**: Agents emit rich progress updates via an `EventBus`. The UI updates instantly—showing the exact skill, file, or test the AI is currently working on.
- **Local First (Ollama)**: Connects to local LLMs (e.g., `qwen2.5-coder:3b`) via Ollama. Supports JSON mode for structured agent outputs and streaming generation.

---

## 📦 Architecture Overview

DevPilot is divided into three core layers:

1. **TUI Layer (`devpilot/tui/`)**
   - Built on Textual.
   - `app.py`: The main event loop and application router.
   - `screens/`: Contains specialized views like `MainScreen`, `CommandPalette`, and `FilePreviewScreen`.
   - `widgets/`: Reusable UI components (e.g., `ChatLog`, `WorkspacePanel`, `LiveFileActivity`).
   
2. **Agent Layer (`devpilot/agents/`)**
   - The brains of the operation. Each agent extends a `BaseAgent` class.
   - Agents emit their state using `self.emit_progress()`, allowing the TUI to reflect exactly what they are thinking and doing.
   
3. **Core Layer (`devpilot/core/`)**
   - `event_bus.py`: The nerve center routing telemetry events between the agents and the UI.
   - `llm.py`: Interfaces with the Ollama API, handling streaming and JSON constraints.
   - `workspace_manager.py`: Manages file state and physical disk writes via Skills.

---

## 💻 Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/devpilot.git
   cd devpilot
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv .venv
   # On Windows:
   .venv\Scripts\activate
   # On macOS/Linux:
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   *(Ensure you install Textual and HTTPx)*
   ```bash
   pip install textual httpx
   ```

4. **Ensure Ollama is running:**
   DevPilot requires Ollama running locally. Start Ollama and ensure your model (e.g., `qwen2.5-coder:3b`) is pulled:
   ```bash
   ollama pull qwen2.5-coder:3b
   ollama run qwen2.5-coder:3b
   ```

---

## 🎮 Usage

Start the Textual application:

```bash
python -m tui.app
```

### Navigating the UI:
- **Chat Input**: Type your coding requests at the bottom of the screen.
- **Command Palette**: Press `Ctrl+P` (or `Cmd+P`) to quickly open files or trigger actions.
- **Workspace Inspector**: The right sidebar shows live AI status, system telemetry, and active file generation.
- **Project Explorer**: The left sidebar shows your local workspace directory tree.

### Example Prompts:
- *"Create a Python script that fetches the current weather for London using the wttr.in API."*
- *"Refactor the authentication logic in `auth.py` to use JWT tokens."*
- *"Write unit tests for the functions in `utils.py`."*

---

## 🛠️ Telemetry & Event System

DevPilot's defining feature is its **transparency**. Rather than waiting for a silent AI to finish, the system routes live telemetry to the UI. 

When the `FilesystemSkill` creates a file, an event is sent over the `EventBus`. The `WorkspacePanel` catches this event and immediately updates the **Live File Activity** list in the TUI, showing a spinner next to the file being edited.

The same applies to testing (`TesterAgent`), planning (`PlannerAgent`), and coding (`CoderAgent`). You are never left wondering what the AI is doing.

---

## 🤝 Contributing

Contributions are welcome! If you're looking to add a new Agent, simply subclass `Agent` in `agents/base.py`, register it in the pipeline, and make sure it emits `emit_progress()` events so the TUI can render it!

## 📜 License

MIT License. See `LICENSE` for more information.