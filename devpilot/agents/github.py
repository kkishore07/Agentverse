"""
agents/github.py
================
GitHub Agent that generates a commit message based on the changes
and then orchestrates the git operations using the SkillRegistry.
"""

from __future__ import annotations

from dataclasses import dataclass
from agents.base import Agent, AgentError
from core.prompts import github_prompt
from core.registry import SkillRegistry


@dataclass(frozen=True)
class GitHubInput:
    goal: str
    changed_files: list[str]
    diff_summary: str
    skill_registry: SkillRegistry


@dataclass(frozen=True)
class GitHubOutput:
    commit_message: str
    commit_hash: str = ""


class GitHubAgent(Agent[GitHubInput, GitHubOutput]):
    """Analyzes changes, generates a commit message, and commits."""

    name = "github"

    async def run(self, agent_input: GitHubInput) -> GitHubOutput:
        self.emit_progress(repository="local", branch="main", modified_files=len(agent_input.changed_files), push_status="Pending", current_milestone="Generating commit message", current_skill="Version Control", progress="0%")
        # Generate the commit message
        system, user = github_prompt(
            goal=agent_input.goal,
            changed_files=agent_input.changed_files,
            diff_summary=agent_input.diff_summary,
        )
        
        full_text = ""
        try:
            stream = self._llm.stream(user, system=system)
            async for chunk in stream:
                full_text += chunk
                self.emit_progress(llm_token=chunk, current_milestone="Generating commit message", current_skill="Version Control", progress="50%")
        except Exception as e:
            raise AgentError(f"GitHub: LLM stream failed: {e}")
            
        commit_message = full_text.strip()
        
        if not commit_message:
            raise AgentError("GitHubAgent failed to generate a commit message.")

        import asyncio
        from core.event_bus import Event
        
        confirm_event = asyncio.Event()
        user_response = False
        
        def on_response(event):
            nonlocal user_response
            user_response = event.data.get("accepted", False)
            confirm_event.set()
            
        self.emit_progress(current_milestone="Awaiting confirmation", current_skill="Version Control", progress="90%")
        self._bus.subscribe("GitHubConfirmResponse", on_response)
        self._bus.publish("GitHubConfirmRequest", message=commit_message, diff=agent_input.diff_summary)
        
        await confirm_event.wait()
        self._bus.unsubscribe("GitHubConfirmResponse", on_response)
        
        if not user_response:
            self.emit_progress(current_milestone="Commit rejected", current_skill="Version Control", progress="100%")
            raise AgentError("User rejected the commit.")
        
        self.emit_progress(push_status="Complete", current_milestone="Committed", current_skill="Version Control", progress="100%")
        
        return GitHubOutput(
            commit_message=commit_message,
            commit_hash="" # Orchestrator or Skill will fill this in
        )
