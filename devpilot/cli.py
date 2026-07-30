"""
cli.py
======
DevPilot's Typer CLI entrypoint.

This module is intentionally thin: it parses commands, wires up
Settings/LLMClient/Orchestrator, and delegates. No pipeline logic lives
here -- that's the Orchestrator's job.

Commands:
    devpilot create "Build a FastAPI Todo Application"
    devpilot explain app/main.py
    devpilot improve app/main.py
    devpilot docs <project-slug>
    devpilot test <project-slug>
"""

from __future__ import annotations

import logging
import subprocess
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from config import get_settings
from core.llm import LLMError, build_default_llm_client
from core.orchestrator import Orchestrator
from core.prompts import explain_prompt, improve_prompt

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

app = typer.Typer(
    name="devpilot",
    help="A local, multi-agent CLI software engineering assistant powered by Ollama.",
    add_completion=False,
)
console = Console()
if hasattr(console.file, "reconfigure"):
    try:
        console.file.reconfigure(encoding="utf-8")
    except Exception:
        pass


def _configure_logging(logs_dir: Path) -> None:
    logs_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(logs_dir / "devpilot.log"),
        ],
    )


@app.command()
def tui() -> None:
    """Launch DevPilot's interactive terminal IDE (Textual UI). This is
    also what running `devpilot` with no subcommand does."""
    from tui.app import run as run_tui

    run_tui()


@app.command()
def create(
    goal: str = typer.Argument(..., help='Project request, e.g. "Build a FastAPI Todo Application"'),
) -> None:
    """Generate a complete software project using the multi-agent pipeline."""
    settings = get_settings()
    _configure_logging(settings.logs_dir)

    llm = build_default_llm_client(settings)
    
    from core.registry import SkillRegistry, AgentRegistry
    from core.event_bus import EventBus
    from core.session import SessionManager
    from pathlib import Path
    
    bus = EventBus()
    session_mgr = SessionManager(Path(settings.workspace_dir) / ".devpilot" / "session.json")
    
    orchestrator = Orchestrator(
        llm=llm,
        session_mgr=session_mgr,
        event_bus=bus,
        skill_registry=SkillRegistry(),
        agent_registry=AgentRegistry(),
        workspace_dir=settings.workspace_dir
    )

    try:
        import asyncio
        result = asyncio.run(orchestrator.run_pipeline("Project Creation", goal))
    except LLMError as exc:
        console.print(
            Panel(
                f"[red]{exc}[/red]\n\n"
                f"Check that Ollama is running (`ollama serve`) and that the model is pulled:\n"
                f"  ollama pull {settings.model_name}",
                title="LLM Unavailable",
                border_style="red",
            )
        )
        raise typer.Exit(code=1)

    if result.success:
        console.print(
            Panel(
                f"[green][+] Project scaffolded successfully![/green]\n\n"
                f"[bold]Root:[/bold] {result.project_root}\n"
                f"[bold]Files Created:[/bold]\n" +
                "\n".join([f"  • {f}" for f in result.written_files]),
                title="DevPilot — Task Completed",
                border_style="green",
            )
        )
    else:
        console.print(
            Panel(
                f"[yellow]Pipeline completed with warnings:[/yellow]\n\n" +
                "\n".join([f"  • {e}" for e in result.errors if e]),
                title="DevPilot — Task Status",
                border_style="yellow",
            )
        )


@app.command()
def explain(
    file_path: str = typer.Argument(..., help="Path to a file, relative to workspace/<project>/ or absolute."),
) -> None:
    """Explain what a generated (or any) source file does."""
    settings = get_settings()
    resolved = _resolve_existing_file(file_path, settings.workspace_dir)

    llm = build_default_llm_client(settings)
    content = resolved.read_text(encoding="utf-8")
    system, user = explain_prompt(str(resolved), content)

    with console.status(f"[cyan]Explaining {resolved.name}...[/cyan]"):
        try:
            import asyncio
            response = asyncio.run(llm.generate(user, system=system))
        except LLMError as exc:
            console.print(f"[red]{exc}[/red]")
            raise typer.Exit(code=1)

    console.print(Panel(Markdown(response.text), title=f"Explain: {resolved.name}", border_style="cyan"))


@app.command()
def improve(
    file_path: str = typer.Argument(..., help="Path to a file, relative to workspace/<project>/ or absolute."),
    write: bool = typer.Option(False, "--write", help="Overwrite the file with the improved version."),
) -> None:
    """Suggest (or apply) improvements to an existing generated file."""
    settings = get_settings()
    resolved = _resolve_existing_file(file_path, settings.workspace_dir)

    llm = build_default_llm_client(settings)
    original = resolved.read_text(encoding="utf-8")
    system, user = improve_prompt(str(resolved), original)

    with console.status(f"[cyan]Improving {resolved.name}...[/cyan]"):
        try:
            import asyncio
            response = asyncio.run(llm.generate(user, system=system))
        except LLMError as exc:
            console.print(f"[red]{exc}[/red]")
            raise typer.Exit(code=1)

    improved = response.text.strip()
    console.print(Panel(improved, title=f"Improved: {resolved.name}", border_style="green"))

    if write:
        resolved.write_text(improved, encoding="utf-8")
        console.print(f"[green]Written to {resolved}[/green]")
    else:
        console.print("[dim]Run again with --write to apply these changes.[/dim]")


@app.command()
def docs(
    project: str = typer.Argument(..., help="Project slug under workspace/, e.g. 'todo-api'."),
) -> None:
    """Regenerate README.md for an existing generated project."""
    settings = get_settings()
    project_root = settings.workspace_dir / project
    if not project_root.is_dir():
        console.print(f"[red]No project found at {project_root}[/red]")
        raise typer.Exit(code=1)

    from agents.docs import DocsInput, DocumentationAgent

    llm = build_default_llm_client(settings)
    agent = DocumentationAgent(llm)

    files = [
        {"path": str(p.relative_to(project_root)), "purpose": ""}
        for p in project_root.rglob("*")
        if p.is_file()
    ]

    with console.status("[cyan]Regenerating README...[/cyan]"):
        try:
            result = agent.run(DocsInput(goal=project, tech_stack=[], files=files))
        except LLMError as exc:
            console.print(f"[red]{exc}[/red]")
            raise typer.Exit(code=1)

    (project_root / "README.md").write_text(result.content, encoding="utf-8")
    console.print(f"[green]README.md updated at {project_root / 'README.md'}[/green]")


@app.command(name="test")
def run_tests(
    project: str = typer.Argument(..., help="Project slug under workspace/, e.g. 'todo-api'."),
) -> None:
    """Run pytest inside a generated project's directory."""
    settings = get_settings()
    project_root = settings.workspace_dir / project
    if not project_root.is_dir():
        console.print(f"[red]No project found at {project_root}[/red]")
        raise typer.Exit(code=1)

    console.print(f"[cyan]Running pytest in {project_root}...[/cyan]")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-v"],
        cwd=str(project_root),
    )
    raise typer.Exit(code=result.returncode)


def _resolve_existing_file(file_path: str, workspace_dir: Path) -> Path:
    """Resolve a user-provided path, trying it as-is, then under workspace/."""
    direct = Path(file_path)
    if direct.is_file():
        return direct
    under_workspace = workspace_dir / file_path
    if under_workspace.is_file():
        return under_workspace
    console.print(f"[red]File not found:[/red] {file_path}")
    raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
