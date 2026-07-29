"""
server.py
=========
DevPilot Web IDE Server — FastAPI bridge between the existing Python
backend and the browser-based IDE frontend.

Launch:  python server.py
Visit:   http://localhost:8000
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Set

# ── path setup ───────────────────────────────────────────────────────────────
# server.py lives at devpilot/, same level as tui/, core/, etc.
sys.path.insert(0, str(Path(__file__).parent))

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from core.event_bus import (
    EVENT_AGENT_FINISHED, EVENT_AGENT_STARTED, EVENT_AGENT_STEP,
    EVENT_ERROR, EVENT_FILE_CONFIRMED, EVENT_FILE_CREATING,
    EVENT_FILE_EDITING, EVENT_FILE_READING, EVENT_TASK_COMPLETE,
    EVENT_TASK_STARTED, EVENT_WARNING,
)
from tui.backend import build_backend, Backend

# ── app setup ─────────────────────────────────────────────────────────────────
from contextlib import asynccontextmanager

_backend: Backend | None = None
_clients: Set[WebSocket] = set()
_event_loop: asyncio.AbstractEventLoop | None = None

# ── broadcast helpers ─────────────────────────────────────────────────────────
async def _broadcast(event_type: str, data: dict) -> None:
    if not _clients:
        return
    payload = json.dumps({"type": event_type, "data": data})
    dead: Set[WebSocket] = set()
    for ws in _clients.copy():
        try:
            await ws.send_text(payload)
        except Exception:
            dead.add(ws)
    _clients -= dead


def _schedule_broadcast(event_type: str, data: dict) -> None:
    """Thread-safe: schedule a broadcast from sync EventBus callbacks."""
    if _event_loop and not _event_loop.is_closed():
        asyncio.run_coroutine_threadsafe(
            _broadcast(event_type, data), _event_loop
        )


def _make_handler(event_name: str):
    async def _handler(event: Any) -> None:
        data = event.data if hasattr(event, "data") else {}
        if not isinstance(data, dict):
            data = {}
        _schedule_broadcast(event_name, data)
    return _handler


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _backend, _event_loop
    _event_loop = asyncio.get_event_loop()
    _backend = build_backend()

    from core.event_bus import EVENT_AGENT_PROGRESS
    all_events = [
        EVENT_AGENT_STARTED, EVENT_AGENT_STEP, EVENT_AGENT_PROGRESS,
        EVENT_AGENT_FINISHED, EVENT_TASK_STARTED, EVENT_TASK_COMPLETE,
        EVENT_FILE_CONFIRMED, EVENT_FILE_CREATING, EVENT_FILE_EDITING,
        EVENT_FILE_READING, EVENT_ERROR, EVENT_WARNING,
        "PipelineStarted", "PipelineStageChanged", "GitHubConfirmRequest",
    ]
    for name in all_events:
        _backend.bus.subscribe(name, _make_handler(name))

    print(f"  [+] Backend ready  --  model: {_backend.settings.model_name}")
    yield

app = FastAPI(title="DevPilot Web IDE", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── static / root ─────────────────────────────────────────────────────────────
WEB_DIR = Path(__file__).parent / "web"

@app.get("/")
async def serve_root():
    return FileResponse(WEB_DIR / "index.html")

app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")


# ── REST API ──────────────────────────────────────────────────────────────────
@app.get("/api/status")
async def api_status():
    if not _backend:
        return JSONResponse({"online": False})
    return JSONResponse({
        "online": True,
        "model": _backend.settings.model_name,
        "workspace": _backend.workspace_info.get("project_name", "devpilot"),
        "branch": _backend.workspace_info.get("git_branch", "main"),
        "language": _backend.workspace_info.get("language", "Python"),
    })


@app.get("/api/files")
async def api_files(path: str = "."):
    return JSONResponse(_build_file_tree(Path(path)))


@app.get("/api/file")
async def api_read_file(path: str):
    return JSONResponse({
        "path": path,
        "content": _read_file(path),
        "language": _detect_language(path),
    })


# ── WebSocket ─────────────────────────────────────────────────────────────────
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    _clients.add(websocket)

    # Send initial handshake
    info: dict = {"type": "connected", "data": {}}
    if _backend:
        info["data"] = {
            "model": _backend.settings.model_name,
            "workspace": _backend.workspace_info.get("project_name", "devpilot"),
            "branch": _backend.workspace_info.get("git_branch", "main"),
        }
    await websocket.send_text(json.dumps(info))

    # Send initial file tree
    await websocket.send_text(json.dumps({
        "type": "file_tree",
        "data": _build_file_tree(Path(".")),
    }))

    try:
        while True:
            raw = await websocket.receive_text()
            await _handle_client_msg(json.loads(raw), websocket)
    except (WebSocketDisconnect, Exception):
        pass
    finally:
        _clients.discard(websocket)


async def _handle_client_msg(msg: dict, ws: WebSocket) -> None:
    action = msg.get("type", "")

    if action == "run_task":
        goal = msg.get("goal", "").strip()
        if goal:
            asyncio.create_task(_run_pipeline(goal))

    elif action == "chat":
        text = msg.get("text", "").strip()
        if text:
            asyncio.create_task(_run_chat(text, ws))

    elif action == "read_file":
        path = msg.get("path", "")
        await ws.send_text(json.dumps({
            "type": "file_content",
            "data": {
                "path": path,
                "content": _read_file(path),
                "language": _detect_language(path),
            },
        }))

    elif action == "get_files":
        await ws.send_text(json.dumps({
            "type": "file_tree",
            "data": _build_file_tree(Path(msg.get("path", "."))),
        }))

    elif action == "github_confirm":
        if _backend:
            _backend.bus.publish(
                "GitHubConfirmResponse",
                accepted=msg.get("accepted", False),
            )


# ── pipeline runner ───────────────────────────────────────────────────────────
async def _run_pipeline(goal: str) -> None:
    if not _backend:
        return
    from core.orchestrator import Orchestrator
    from core.registry import AgentRegistry, SkillRegistry

    orchestrator = Orchestrator(
        llm=_backend.llm,
        session_mgr=_backend.session_mgr,
        event_bus=_backend.bus,
        skill_registry=SkillRegistry(),
        agent_registry=AgentRegistry(),
        workspace_dir=_backend.workspace_info.get("path", "."),
    )
    _backend.bus.publish(EVENT_TASK_STARTED, goal=goal)
    result = await orchestrator.run_pipeline("Project Creation", goal)
    _backend.bus.publish(
        EVENT_TASK_COMPLETE,
        goal=goal,
        success=result.success,
        project_root=str(result.project_root),
        written_files=result.written_files,
        errors=result.errors,
    )


async def _run_chat(text: str, ws: WebSocket) -> None:
    if not _backend:
        return

    async def on_token(token: str) -> None:
        try:
            await ws.send_text(
                json.dumps({"type": "chat_token", "data": {"token": token}})
            )
        except Exception:
            pass

    full = await _backend.chat_engine.respond_stream(text, on_token=on_token)
    try:
        await ws.send_text(
            json.dumps({"type": "chat_done", "data": {"text": full}})
        )
    except Exception:
        pass


# ── filesystem helpers ────────────────────────────────────────────────────────
_SKIP = {
    ".git", "__pycache__", ".venv", "node_modules",
    ".pytest_cache", "dist", "build", ".eggs", ".mypy_cache",
}

def _build_file_tree(root: Path, depth: int = 0) -> dict:
    if depth > 7:
        return {}
    node: dict = {"name": root.name or str(root), "path": str(root)}
    if root.is_dir():
        node["type"] = "dir"
        children = []
        try:
            items = sorted(
                root.iterdir(),
                key=lambda p: (p.is_file(), p.name.lower()),
            )
            for child in items:
                if child.name in _SKIP or child.name.startswith("."):
                    continue
                sub = _build_file_tree(child, depth + 1)
                if sub:
                    children.append(sub)
        except PermissionError:
            pass
        node["children"] = children
    else:
        node["type"] = "file"
    return node


def _read_file(path: str) -> str:
    try:
        p = Path(path)
        if p.is_file() and p.stat().st_size < 500_000:
            return p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        pass
    return ""


def _detect_language(path: str) -> str:
    ext = Path(path).suffix.lower()
    return {
        ".py": "python", ".js": "javascript", ".jsx": "javascript",
        ".ts": "typescript", ".tsx": "typescript", ".html": "html",
        ".css": "css", ".json": "json", ".yaml": "yaml", ".yml": "yaml",
        ".md": "markdown", ".sh": "shell", ".bash": "shell",
        ".toml": "toml", ".rs": "rust", ".go": "go", ".java": "java",
        ".cpp": "cpp", ".c": "c", ".cs": "csharp", ".rb": "ruby",
        ".php": "php", ".swift": "swift", ".kt": "kotlin",
    }.get(ext, "plaintext")


# ── entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print()
    print("  [*] DevPilot Web IDE")
    print("  -----------------------------------------")
    print("  -> http://localhost:8000")
    print("  Press Ctrl+C to stop")
    print()
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")
