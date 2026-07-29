# DevPilot

A local, multi-agent CLI software engineering assistant. DevPilot orchestrates
a small team of specialized AI agents — Planner, Architect, Coder, Tester, and
Documentation — to turn a one-line request into a complete, runnable project,
using **only a local Ollama model** (`qwen2.5-coder:3b` by default). No cloud
LLM APIs are used.

```
devpilot create "Build a FastAPI Todo Application"
```

## Why it's built this way

The core design rule is: **agents never call each other.** Every agent is a
pure function of (typed input) -> (typed output), implemented against the
`Agent` base class and depending only on the `LLMClient` interface — never a
concrete Ollama class, never another agent. The `Orchestrator` is the only
component that knows the pipeline's shape and sequences agents, retries
failures, and threads a shared `ProjectMemory` object through the run.

That separation is what makes the two future-facing requirements — "add new
agents without touching existing ones" and "swap the LLM backend" — cheap
instead of theoretical:

- **Swap models**: edit `core/llm.py` only. Everything else depends on the
  `LLMClient` Protocol, not on Ollama specifically.
- **Add an agent** (Security, Git, Docker, CI/CD, ...): implement `Agent`,
  add its prompt to `core/prompts.py`, add one step to `Orchestrator`. No
  existing agent's code changes.

## Architecture

```
User → Typer CLI → Orchestrator
                        │
        ┌───────────────┼──────────────────────┐
        ▼               ▼                       ▼
  Planner Agent   Architect Agent         ProjectMemory
        │                                  (goal, tasks,
        ▼                                  architecture,
  for each file:                           files, errors)
     Coder Agent → Tester Agent
        │
        ▼
  Documentation Agent
        │
        ▼
  Project Writer → workspace/<project-slug>/
```

| Component | Responsibility |
|---|---|
| `core/llm.py` | The **only** module that talks to Ollama's HTTP API (`/api/generate`). Retries, timeouts, JSON-mode. |
| `core/prompts.py` | Every agent's system/user prompt templates, kept separate from execution logic. |
| `core/memory.py` | Plain-dataclass runtime state for one run — goal, plan, architecture, generated files, errors. No vector DB. |
| `core/orchestrator.py` | Sequences agents, retries failed steps, renders Rich progress, writes the memory log. |
| `agents/planner.py` | Free-form request → project name + ordered task list (JSON). |
| `agents/architect.py` | Tasks → tech stack, folders, file manifest (JSON), with path-safety sanitization. |
| `agents/coder.py` | One file's content at a time — never the whole project in one prompt. |
| `agents/tester.py` | Pytest tests for a given source file, generated after that file exists. |
| `agents/docs.py` | README, generated last so it can describe the final file set. |
| `agents/writer.py` | The only component that touches the filesystem; uses `utils/fs.safe_join` to prevent path traversal from LLM-suggested paths. |
| `cli.py` | Typer commands; thin — wires Settings → LLMClient → Orchestrator and delegates. |

## Requirements

- Python 3.12+
- [Ollama](https://ollama.com) running locally with the model pulled:

```bash
ollama pull qwen2.5-coder:3b
ollama serve
```

## Installation

```bash
cd devpilot
pip install -r requirements.txt
```

## Usage

```bash
# Generate a full project into workspace/<slug>/
python -m cli create "Build a FastAPI Todo Application"

# Ask an agent to explain a file
python -m cli explain workspace/todo-api/app/main.py

# Get (and optionally apply) an improvement pass on a file
python -m cli improve workspace/todo-api/app/main.py --write

# Regenerate README.md for an already-generated project
python -m cli docs todo-api

# Run the generated project's own pytest suite
python -m cli test todo-api
```

Generated projects land in `workspace/<project-slug>/`. Every run's full
state (plan, architecture, files, errors, timings) is also dumped as JSON to
`logs/` for auditing.

## Configuration

All configuration is environment-variable driven (see `config.py`):

| Variable | Default |
|---|---|
| `DEVPILOT_OLLAMA_HOST` | `http://localhost:11434` |
| `DEVPILOT_MODEL` | `qwen2.5-coder:3b` |
| `DEVPILOT_LLM_TIMEOUT` | `180` (seconds) |
| `DEVPILOT_LLM_RETRIES` | `3` |
| `DEVPILOT_TEMPERATURE` | `0.2` |
| `DEVPILOT_MAX_FILES` | `40` |

## Terminal IDE (Textual UI)

DevPilot's primary interface is now a full Textual TUI (`tui/`), replacing
the previous prompt_toolkit console:

```bash
devpilot            # launches the TUI (default)
python -m tui.app   # same, if running from source
devpilot-cli create "..."   # the old one-shot Typer commands still work
```

- **Chat area** — streaming, syntax-highlighted markdown responses.
- **Activity log** — collapsible per-agent panels with live progress bars,
  fed by the existing `EventBus` (no business logic changed).
- **Slash commands** (`/agents`, `/models`, `/skills`, `/settings`, `/theme`,
  `/status`, `/project`, `/history`, `/clear`, `/help`) open a real
  keyboard-navigable popup (↑ ↓ Enter Esc), not printed text.
- **Modal screens** for Agents / Models / Skills / Settings / Help — all
  `OptionList`/`DataTable`-driven.
- **Shortcuts** — Ctrl+P command palette, Ctrl+A agents, Ctrl+M models,
  Ctrl+S settings, Ctrl+H help, Ctrl+L clear.
- **Themes** — Tokyo Night, Gruvbox, Catppuccin Mocha, Nord, One Dark,
  switchable via `/settings`, the command palette, or `/theme`.

Layout, wiring, and event handling live entirely in `tui/`; `core/`,
`agents/`, `skills/`, and `commands/` are unchanged — the TUI is a new
presentation layer over the same async pipeline.

### Known issue

`tests/` in this repo predates a refactor that made `Agent.run()` async
and added an `EventBus` parameter to every agent's constructor — the
legacy tests weren't updated and currently fail on construction, not on
behavior. This is unrelated to the TUI work above; fixing it means
updating `tests/conftest.py`'s mock and the affected test signatures to
match the current async `Agent`/`Orchestrator` APIs.


The test suite mocks the `LLMClient` interface (`tests/conftest.py`), so it
runs fully offline — no Ollama server required — and covers JSON
extraction/repair, path-traversal safety, each agent in isolation, and a
full end-to-end pipeline run against a scripted mock model.

```bash
pytest -v
```

## Extending DevPilot

Because agents never call each other, adding a new agent (e.g. a future
`SecurityAgent`, `GitAgent`, `DockerAgent`, `ReviewAgent`, `BugFixAgent`)
means:

1. Add its prompt template(s) to `core/prompts.py`.
2. Implement it in `agents/<name>.py`, subclassing `agents.base.Agent`.
3. Instantiate it in `Orchestrator.__init__` and add one `_run_step(...)`
   call to `create_project` (or a new command in `cli.py` if it's not part
   of the main pipeline).

No existing agent, prompt, or CLI command needs to change.

## Known limitations

- Small local models (3B class) sometimes produce imperfect JSON or code on
  the first try; the Orchestrator retries each step a bounded number of
  times and records unresolved failures in the run log rather than crashing.
- Generated code is a strong starting point, not a guarantee of
  correctness — always review before shipping, and use `devpilot test` /
  `devpilot improve` as a next pass.
