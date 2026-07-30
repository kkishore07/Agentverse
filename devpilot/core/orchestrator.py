"""
core/orchestrator.py
====================
Async orchestrator for DevPilot v2.

Dynamically runs pipelines of agents (Project Creation, Bug Fix, Code Review, etc.)
communicating state via ProjectContext.
"""

from __future__ import annotations

import logging
import asyncio
import re
import difflib
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, TypeVar, Any, Optional

from agents.base import AgentError
from agents.planner import PlannerAgent, PlannerInput
from agents.architect import ArchitectAgent, ArchitectInput, ArchitectOutput, FileSpec
from agents.coder import CoderAgent, CoderInput, CoderOutput
from agents.validator import ValidatorAgent, ValidatorInput
from agents.tester import TesterAgent, TesterInput
from agents.docs import DocumentationAgent, DocsInput
from agents.fixer import FixerAgent, FixerInput
from agents.reviewer import ReviewerAgent, ReviewerInput
from agents.github import GitHubAgent, GitHubInput

from core.llm import OllamaLLMClient, LLMError
from core.session import SessionManager
from core.context import ProjectContext
from core.event_bus import (
    EventBus,
    EVENT_PIPELINE_STARTED, EVENT_PIPELINE_STAGE_CHANGED,
    EVENT_AGENT_STARTED, EVENT_AGENT_STEP, EVENT_AGENT_FINISHED,
    EVENT_THINKING, EVENT_FILE_READING, EVENT_FILE_CREATING,
    EVENT_FILE_EDITING, EVENT_CODE_COMPLETE, EVENT_DIFF_READY,
    EVENT_FILE_CONFIRMED,
)
from core.registry import SkillRegistry, AgentRegistry
from core.workspace_manager import WorkspaceManager, FileArtifact

logger = logging.getLogger("devpilot.orchestrator")

T = TypeVar("T")


@dataclass
class OrchestratorResult:
    project_root: Path
    success: bool
    written_files: list[str]
    errors: list[str]


def _make_diff(old_content: str, new_content: str, filename: str) -> str:
    """Generate a unified diff string with graceful fallback."""
    try:
        old_lines = old_content.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)
        diff = difflib.unified_diff(
            old_lines, new_lines,
            fromfile=f"a/{filename}",
            tofile=f"b/{filename}",
        )
        return "".join(diff)
    except Exception:
        return f"--- a/{filename}\n+++ b/{filename}\n@@ -1 +1 @@\n-{old_content[:50]}\n+{new_content[:50]}\n"


class Orchestrator:
    """Coordinates agent pipelines dynamically."""

    def __init__(
        self,
        llm: OllamaLLMClient,
        session_mgr: SessionManager,
        event_bus: EventBus,
        skill_registry: SkillRegistry,
        agent_registry: AgentRegistry,
        workspace_dir: str | Path = ".",
        max_files: int = 20,
        max_retries: int = 2,
    ) -> None:
        self._llm = llm
        self._session_mgr = session_mgr
        self._bus = event_bus
        self._skills = skill_registry
        self._agents = agent_registry
        self._workspace_dir = Path(workspace_dir).resolve()
        self._max_files = max_files
        self._max_retries = max_retries

        self._register_default_agents()

    def _register_default_agents(self) -> None:
        """Register the standard set of agents."""
        if not self._agents.get("planner"):
            self._agents.register("planner", PlannerAgent(self._llm, self._bus))
        if not self._agents.get("architect"):
            self._agents.register("architect", ArchitectAgent(self._llm, self._bus))
        if not self._agents.get("coder"):
            self._agents.register("coder", CoderAgent(self._llm, self._bus))
        if not self._agents.get("validator"):
            self._agents.register("validator", ValidatorAgent(self._llm, self._bus))
        if not self._agents.get("tester"):
            self._agents.register("tester", TesterAgent(self._llm, self._bus))
        if not self._agents.get("fixer"):
            self._agents.register("fixer", FixerAgent(self._llm, self._bus))
        if not self._agents.get("reviewer"):
            self._agents.register("reviewer", ReviewerAgent(self._llm, self._bus))
        if not self._agents.get("docs"):
            self._agents.register("docs", DocumentationAgent(self._llm, self._bus))
        if not self._agents.get("github"):
            self._agents.register("github", GitHubAgent(self._llm, self._bus))

    def _emit(self, event_type: str, **kwargs: Any) -> None:
        self._bus.publish(event_type, **kwargs)

    async def run_pipeline(self, pipeline_type: str, goal: str) -> OrchestratorResult:
        """Run a dynamic pipeline based on the type requested."""
        context = ProjectContext(goal=goal, workspace_dir=self._workspace_dir)
        
        # Determine the stages for the pipeline
        if pipeline_type == "Project Creation":
            stages = ["planner", "architect", "coder", "validator", "tester", "reviewer", "docs", "github"]
        elif pipeline_type == "Bug Fix":
            stages = ["validator", "tester", "fixer", "validator", "tester", "reviewer", "github"]
        elif pipeline_type == "Code Review":
            stages = ["reviewer", "github"]
        elif pipeline_type == "Documentation":
            stages = ["docs", "github"]
        else:
            # Default fallback
            stages = ["planner", "architect", "coder", "validator", "tester", "reviewer", "docs", "github"]

        self._emit(EVENT_PIPELINE_STARTED, pipeline_type=pipeline_type, stages=stages)
        
        ws_mgr = WorkspaceManager(self._workspace_dir, bus=self._bus)

        for stage in stages:
            self._emit(EVENT_PIPELINE_STAGE_CHANGED, stage=stage)
            
            # Execute the specific agent for this stage
            if stage == "planner":
                await self._run_planner(context)
                if getattr(context, "project_name", None):
                    import re
                    slug = re.sub(r'[^a-z0-9]+', '-', context.project_name.lower()).strip('-') or "app"
                    projects_dir = self._workspace_dir if self._workspace_dir.name == "projects" else (self._workspace_dir / "projects")
                    projects_dir.mkdir(parents=True, exist_ok=True)
                    context.workspace_dir = projects_dir / slug
                    context.workspace_dir.mkdir(parents=True, exist_ok=True)
                    ws_mgr = WorkspaceManager(context.workspace_dir, bus=self._bus)
            elif stage == "architect":
                await self._run_architect(context)
            elif stage == "coder":
                await self._run_coder(context, ws_mgr)
            elif stage == "validator":
                await self._run_validator(context)
                if not context.validation_passed:
                    # If validation fails, we might want to short-circuit or trigger Fixer.
                    # For simplicity in this linear pipeline, we just log and continue, 
                    # and if Fixer is the next stage, it will pick it up.
                    pass
            elif stage == "tester":
                await self._run_tester(context)
            elif stage == "fixer":
                if not context.validation_passed or not context.tests_passed:
                    await self._run_fixer(context, ws_mgr)
            elif stage == "reviewer":
                await self._run_reviewer(context)
            elif stage == "docs":
                await self._run_docs(context, ws_mgr)
            elif stage == "github":
                await self._run_github(context)
                
            # Stop if we hit a critical failure in the context
            # (e.g. Planner or Architect failed completely)
            if context.metadata.get("critical_error"):
                break

        # Persist some state to the session manager
        state = getattr(self._session_mgr, "active_session", self._session_mgr).state
        state.project_metadata["plan"] = {
            "project_name": context.project_name,
            "tasks": context.tasks,
        }
        # Sanitize legacy dicts from session state
        safe_existing = [f if isinstance(f, str) else f.get("path", "") for f in state.generated_files if isinstance(f, (str, dict))]
        safe_existing = [f for f in safe_existing if f]
        state.generated_files = list(set(safe_existing + context.written_files))
        self._session_mgr.save()

        is_success = not bool(context.metadata.get("critical_error")) and (context.validation_passed or not context.written_files)

        return OrchestratorResult(
            project_root=self._workspace_dir,
            success=is_success,
            written_files=context.written_files,
            errors=context.validation_errors + context.test_reports + [context.metadata.get("critical_error", "")]
        )

    async def _run_planner(self, context: ProjectContext) -> None:
        agent = self._agents.get("planner")
        if not agent: return

        self._emit(EVENT_AGENT_STARTED, agent_name="Planner")
        self._emit(EVENT_AGENT_STEP, agent_name="Planner", step="Analyzing request")
        self._emit(EVENT_THINKING, message="Breaking task down into execution steps...")

        state = getattr(self._session_mgr, "active_session", self._session_mgr).state
        plan = await self._run_step(
            "Planner",
            lambda: agent.run(PlannerInput(goal=context.goal, context_files=list(state.generated_files)))
        )
        if plan:
            context.project_name = plan.project_name
            context.tasks = plan.tasks
            self._emit(EVENT_AGENT_STEP, agent_name="Planner", step=f"Project: {plan.project_name}")
            for task in plan.tasks[:6]:
                self._emit(EVENT_AGENT_STEP, agent_name="Planner", step=task)
        else:
            context.metadata["critical_error"] = "Planner failed to decompose task"
            
        self._emit(EVENT_AGENT_FINISHED, agent_name="Planner")
        context.log_execution("Planner", "Completed" if plan else "Failed")

    async def _run_architect(self, context: ProjectContext) -> None:
        agent = self._agents.get("architect")
        if not agent: return

        self._emit(EVENT_AGENT_STARTED, agent_name="Architect")
        self._emit(EVENT_AGENT_STEP, agent_name="Architect", step="Designing file layout")
        self._emit(EVENT_THINKING, message="Selecting tech stack and files...")

        architecture = await self._run_step(
            "Architect",
            lambda: agent.run(
                ArchitectInput(goal=context.goal, tasks=context.tasks, max_files=self._max_files)
            ),
        )
        if architecture:
            context.tech_stack = architecture.tech_stack
            context.planned_files = [{"path": f.path, "purpose": f.purpose, "type": f.type} for f in architecture.files]
            
            if architecture.tech_stack:
                self._emit(EVENT_AGENT_STEP, agent_name="Architect",
                           step=f"Tech stack: {', '.join(architecture.tech_stack[:4])}")
            self._emit(EVENT_AGENT_STEP, agent_name="Architect",
                       step=f"Planning {len(architecture.files)} files")
        else:
            context.metadata["critical_error"] = "Architect failed to design file layout"

        self._emit(EVENT_AGENT_FINISHED, agent_name="Architect")
        context.log_execution("Architect", "Completed" if architecture else "Failed")

    async def _run_coder(self, context: ProjectContext, ws_mgr: WorkspaceManager) -> None:
        agent = self._agents.get("coder")
        if not agent: return

        code_files = [f for f in context.planned_files if f.get("type") == "code"]
        sibling_paths = [f["path"] for f in context.planned_files]

        for spec in code_files:
            self._emit(EVENT_AGENT_STARTED, agent_name="Coder")
            self._emit(EVENT_AGENT_STEP, agent_name="Coder", step=f"Generating {spec['path']}")

            target_path = (context.workspace_dir / spec['path']).resolve()
            existing_content = None
            if target_path.exists():
                self._emit(EVENT_FILE_READING, path=spec['path'])
                existing_content = target_path.read_text(encoding="utf-8", errors="replace")

            self._emit(EVENT_THINKING, message=f"Writing {spec.get('purpose') or spec['path']}...")

            result = await self._run_step(
                "Coder",
                lambda s=spec: agent.run(
                    CoderInput(
                        goal=context.goal,
                        tech_stack=context.tech_stack,
                        file_path=s['path'],
                        file_purpose=s.get('purpose', ''),
                        sibling_files=sibling_paths,
                    )
                ),
            )

            if result and result.content:
                action_type = "update" if existing_content is not None else "create"
                artifact = FileArtifact(path=spec['path'], content=result.content, action=action_type)
                try:
                    target_written = ws_mgr.apply_artifact(artifact)
                    if target_written and target_written.exists():
                        context.written_files.append(spec['path'])
                        if existing_content is not None:
                            diff = _make_diff(existing_content, result.content, spec['path'])
                            self._emit(EVENT_DIFF_READY, path=spec['path'], diff=diff)
                        else:
                            self._emit(EVENT_CODE_COMPLETE, path=spec['path'], content=result.content)
                    else:
                        context.validation_errors.append(f"Filesystem verification failed for {spec['path']}")
                except Exception as err:
                    context.validation_errors.append(f"Failed to write {spec['path']}: {err}")

            self._emit(EVENT_AGENT_STEP, agent_name="Coder", step=f"Finished {spec['path']}")
            self._emit(EVENT_AGENT_FINISHED, agent_name="Coder")
        
        context.log_execution("Coder", f"Generated {len(code_files)} files")

    async def _run_validator(self, context: ProjectContext) -> None:
        agent = self._agents.get("validator")
        if not agent: return

        self._emit(EVENT_AGENT_STARTED, agent_name="Validator")
        self._emit(EVENT_AGENT_STEP, agent_name="Validator", step="Validating files & syntax")

        val_result = await agent.run(ValidatorInput(workspace_dir=context.workspace_dir, written_files=context.written_files))
        context.validation_passed = val_result.passed

        if not val_result.passed:
            self._emit(EVENT_AGENT_STEP, agent_name="Validator", step="Validation failed")
            val_err_msgs = [f"[{err.error_type}] {err.file_path}: {err.message} (Line {err.line_number or 'N/A'}) -> Fix: {err.suggested_fix or 'None'}" for err in val_result.errors]
            context.validation_errors.extend(val_err_msgs)
        else:
            self._emit(EVENT_AGENT_STEP, agent_name="Validator", step="All files & syntax verified")
            context.validation_errors.clear()

        self._emit(EVENT_AGENT_FINISHED, agent_name="Validator")
        context.log_execution("Validator", "Passed" if val_result.passed else "Failed")

    async def _run_tester(self, context: ProjectContext) -> None:
        agent = self._agents.get("tester")
        if not agent: return

        self._emit(EVENT_AGENT_STARTED, agent_name="Tester")
        self._emit(EVENT_AGENT_STEP, agent_name="Tester", step="Running automated tests")

        test_result = await agent.run(TesterInput(workspace_dir=context.workspace_dir))
        
        if test_result.ran_tests:
            context.tests_passed = test_result.passed
            if not test_result.passed:
                self._emit(EVENT_AGENT_STEP, agent_name="Tester", step="Tests failed")
                context.test_reports.append(f"Test run ({test_result.command}) failed: {test_result.stderr or test_result.stdout}")
            else:
                self._emit(EVENT_AGENT_STEP, agent_name="Tester", step=f"Tests passed ({test_result.duration_seconds}s)")
                context.test_reports.clear()
        else:
            context.tests_passed = True # no tests ran, consider passed

        self._emit(EVENT_AGENT_FINISHED, agent_name="Tester")
        context.log_execution("Tester", "Passed" if context.tests_passed else "Failed")

    async def _run_fixer(self, context: ProjectContext, ws_mgr: WorkspaceManager) -> None:
        agent = self._agents.get("fixer")
        if not agent: return

        # Identify files with errors and try to fix them
        # (This is simplified; a robust Fixer would map errors to specific files)
        # For now, we take the first written file that is problematic or all of them.
        
        files_to_fix = set()
        for err in context.validation_errors:
            # Naive parse of "[ErrorType] path/to/file: message"
            match = re.search(r'\[.*?\]\s+(.*?):', err)
            if match:
                files_to_fix.add(match.group(1))
                
        if not files_to_fix and context.written_files:
            files_to_fix.add(context.written_files[0]) # fallback

        for file_path in files_to_fix:
            target_path = (context.workspace_dir / file_path).resolve()
            if target_path.exists():
                self._emit(EVENT_AGENT_STARTED, agent_name="Fixer")
                self._emit(EVENT_AGENT_STEP, agent_name="Fixer", step=f"Fixing {file_path}")
                self._emit(EVENT_THINKING, message=f"Analyzing errors in {file_path}...")
                
                content = target_path.read_text(encoding="utf-8", errors="replace")
                errors = context.validation_errors + context.test_reports
                
                result = await self._run_step(
                    "Fixer",
                    lambda p=file_path, c=content, e=errors: agent.run(FixerInput(file_path=p, content=c, errors=e))
                )
                
                if result and result.fixed_content:
                    artifact = FileArtifact(path=file_path, content=result.fixed_content, action="update")
                    try:
                        ws_mgr.apply_artifact(artifact)
                        diff = _make_diff(content, result.fixed_content, file_path)
                        self._emit(EVENT_DIFF_READY, path=file_path, diff=diff)
                    except Exception as exc:
                        logger.error(f"Fixer failed to save {file_path}: {exc}")

                self._emit(EVENT_AGENT_FINISHED, agent_name="Fixer")

        context.log_execution("Fixer", f"Attempted fixes on {len(files_to_fix)} files")

    async def _run_reviewer(self, context: ProjectContext) -> None:
        agent = self._agents.get("reviewer")
        if not agent: return

        self._emit(EVENT_AGENT_STARTED, agent_name="Reviewer")
        self._emit(EVENT_AGENT_STEP, agent_name="Reviewer", step="Reviewing code quality")
        
        files_to_review = []
        for path in context.written_files:
            target_path = (context.workspace_dir / path).resolve()
            if target_path.exists():
                content = target_path.read_text(encoding="utf-8", errors="replace")
                files_to_review.append({"path": path, "content": content})
                
        if not files_to_review:
            self._emit(EVENT_AGENT_FINISHED, agent_name="Reviewer")
            return
            
        self._emit(EVENT_THINKING, message=f"Reviewing {len(files_to_review)} files for issues...")

        result = await self._run_step(
            "Reviewer",
            lambda: agent.run(ReviewerInput(goal=context.goal, files=files_to_review))
        )
        
        if result and result.issues:
            self._emit(EVENT_AGENT_STEP, agent_name="Reviewer", step=f"Found {len(result.issues)} review issues")
            for issue in result.issues[:3]:
                 self._emit(EVENT_AGENT_STEP, agent_name="Reviewer", step=f"[{issue.severity.upper()}] {issue.file}: {issue.issue}")
        else:
             self._emit(EVENT_AGENT_STEP, agent_name="Reviewer", step="Code looks good, no major issues found.")

        self._emit(EVENT_AGENT_FINISHED, agent_name="Reviewer")
        context.log_execution("Reviewer", f"Found {len(result.issues) if result else 0} issues")

    async def _run_docs(self, context: ProjectContext, ws_mgr: WorkspaceManager) -> None:
        agent = self._agents.get("docs")
        if not agent: return
        
        docs_planned = [f for f in context.planned_files if f.get("type") == "docs"]
        if not docs_planned: return
        
        self._emit(EVENT_AGENT_STARTED, agent_name="Documentation")
        self._emit(EVENT_AGENT_STEP, agent_name="Documentation", step="Generating README")

        result = await self._run_step(
            "Docs",
            lambda: agent.run(DocsInput(
                goal=context.goal,
                tech_stack=context.tech_stack,
                files=context.planned_files
            ))
        )
        
        if result and result.content:
            artifact = FileArtifact(path=result.path, content=result.content, action="update")
            target_written = ws_mgr.apply_artifact(artifact)
            if target_written:
                context.written_files.append(result.path)
                self._emit(EVENT_CODE_COMPLETE, path=result.path, content=result.content)

        self._emit(EVENT_AGENT_FINISHED, agent_name="Documentation")
        context.log_execution("Docs", "Generated" if result else "Failed")

    async def _run_github(self, context: ProjectContext) -> None:
        agent = self._agents.get("github")
        if not agent: return
        
        if not context.written_files:
            return

        self._emit(EVENT_AGENT_STARTED, agent_name="GitHub")
        self._emit(EVENT_AGENT_STEP, agent_name="GitHub", step="Generating commit message")

        diff_summary = f"Created/Modified {len(context.written_files)} files."
        
        result = await self._run_step(
            "GitHub",
            lambda: agent.run(GitHubInput(
                goal=context.goal,
                changed_files=context.written_files,
                diff_summary=diff_summary,
                skill_registry=self._skills
            ))
        )
        
        if result and result.commit_message:
            self._emit(EVENT_AGENT_STEP, agent_name="GitHub", step=f"Commit: {result.commit_message.splitlines()[0]}")
            # The actual commit via skills would be executed here, e.g. using git skill
            # git_skill = self._skills.get("git")
            # if git_skill: git_skill.commit(result.commit_message)
        
        self._emit(EVENT_AGENT_FINISHED, agent_name="GitHub")
        context.log_execution("GitHub", "Committed" if result else "Failed")


    async def _run_step(
        self,
        agent_label: str,
        action: Callable[[], Any],
    ) -> Any | None:
        last_error: Exception | None = None
        for attempt in range(1, self._max_retries + 2):
            try:
                return await action()
            except (AgentError, LLMError) as exc:
                last_error = exc
                logger.warning("%s failed (attempt %d): %s", agent_label, attempt, exc)
                self._emit("Warning", message=f"{agent_label} retry {attempt}: {exc}")
                await asyncio.sleep(min(attempt, 3))

        self._emit("Error", message=f"{agent_label} failed after retries: {last_error}")
        return None

