"""
core/prompt_engine.py
=====================
PromptEngine — the sole component responsible for assembling prompts.

Pipeline:
  Agent → PromptEngine → PromptOptimizer → ModelRouter → LLM → OutputValidator → RetryEngine → Structured Output

The PromptEngine:
  1. Loads a single, comprehensive markdown file per agent (e.g., prompts/planner.md)
  2. Injects dynamic runtime context (goal, files, project context, etc.)
  3. Injects the Pydantic output schema as JSON
  4. Returns a PromptBundle with separate system_prompt and user_prompt
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Type
from pydantic import BaseModel


PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

# Maximum characters of a single file's content to inject into the prompt.
# Prevents context window overflow for large files.
MAX_FILE_CHARS = 8_000


@dataclass
class PromptBundle:
    """The final assembled prompt, split into system and user components."""
    system_prompt: str
    user_prompt: str
    agent_name: str
    token_estimate: int = 0


class PromptEngine:
    """
    Loads a comprehensive agent prompt from disk and assembles it with
    dynamic runtime context for a PromptBundle.

    Usage:
        engine = PromptEngine()
        bundle = engine.get_prompt("planner", context, schema_class=PlannerOutput)
    """

    def __init__(self, prompts_dir: Optional[Path] = None):
        self._dir = prompts_dir or PROMPTS_DIR

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_prompt(
        self,
        agent_name: str,
        context: Dict[str, Any],
        schema_class: Optional[Type[BaseModel]] = None,
    ) -> PromptBundle:
        """
        Assemble and return a PromptBundle for the given agent.

        Args:
            agent_name:   Name of the agent (matches filename in prompts/).
            context:      Runtime context dict with keys like 'goal', 'files', etc.
            schema_class: Optional Pydantic model class whose schema will be injected.
        """
        system_prompt = self._load_system_prompt(agent_name, schema_class)
        user_prompt = self._build_user_prompt(context)

        token_estimate = (len(system_prompt) + len(user_prompt)) // 4  # rough estimate

        return PromptBundle(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            agent_name=agent_name,
            token_estimate=token_estimate,
        )

    # ------------------------------------------------------------------
    # System Prompt: Load from disk + inject schema
    # ------------------------------------------------------------------

    def _load_system_prompt(
        self,
        agent_name: str,
        schema_class: Optional[Type[BaseModel]],
    ) -> str:
        prompt_file = self._dir / f"{agent_name}.md"
        if not prompt_file.exists():
            raise FileNotFoundError(
                f"PromptEngine: No prompt file found for agent '{agent_name}'. "
                f"Expected: {prompt_file}"
            )

        base = prompt_file.read_text(encoding="utf-8").strip()

        if schema_class:
            import json
            schema = schema_class.model_json_schema()
            schema_str = json.dumps(schema, indent=2)
            base += f"\n\n## REQUIRED OUTPUT SCHEMA\nYou must output ONLY valid JSON that strictly matches the following JSON Schema:\n```json\n{schema_str}\n```\n"

        return base

    # ------------------------------------------------------------------
    # User Prompt: Assemble runtime context
    # ------------------------------------------------------------------

    def _build_user_prompt(self, context: Dict[str, Any]) -> str:
        parts: List[str] = []

        # ── Core goal ──────────────────────────────────────────────────
        if context.get("goal"):
            parts.append(f"## CURRENT GOAL\n{context['goal']}")

        # ── Project context ────────────────────────────────────────────
        if context.get("project_context"):
            pc = context["project_context"]
            pc_str = json.dumps(pc, indent=2) if isinstance(pc, dict) else str(pc)
            parts.append(f"## PROJECT CONTEXT\n```json\n{pc_str}\n```")

        # ── Architecture blueprint from Architect agent ─────────────────
        if context.get("architecture"):
            arch = context["architecture"]
            arch_str = json.dumps(arch, indent=2) if isinstance(arch, dict) else str(arch)
            parts.append(f"## ARCHITECTURE BLUEPRINT\n```json\n{arch_str}\n```")

        # ── Previous agent output (e.g. PlannerOutput JSON) ────────────
        if context.get("previous_output"):
            prev = context["previous_output"]
            prev_str = json.dumps(prev, indent=2) if isinstance(prev, dict) else str(prev)
            parts.append(f"## PREVIOUS AGENT OUTPUT\n```json\n{prev_str}\n```")

        # ── Relevant files (injected selectively, not the full workspace) ─
        if context.get("files"):
            file_blocks: List[str] = []
            for f in context["files"]:
                path = f.get("path", "unknown")
                content = f.get("content", "")
                # Truncate very large files to avoid flooding the context window
                if len(content) > MAX_FILE_CHARS:
                    content = content[:MAX_FILE_CHARS] + f"\n... [truncated — {len(content)} total chars]"
                file_blocks.append(f"### {path}\n```\n{content}\n```")
            parts.append("## RELEVANT FILES\n" + "\n\n".join(file_blocks))

        # ── Git state ──────────────────────────────────────────────────
        if context.get("git_status"):
            parts.append(f"## GIT STATUS\n```\n{context['git_status']}\n```")

        if context.get("git_diff"):
            diff = context["git_diff"]
            if len(diff) > 12_000:
                diff = diff[:12_000] + "\n... [diff truncated]"
            parts.append(f"## GIT DIFF\n```diff\n{diff}\n```")

        if context.get("diff_summary"):
            parts.append(f"## DIFF SUMMARY\n{context['diff_summary']}")

        # ── Errors (for Fixer agent) ───────────────────────────────────
        if context.get("errors"):
            err_list = context["errors"]
            if isinstance(err_list, list):
                err_text = "\n".join(err_list)
            else:
                err_text = str(err_list)
            parts.append(f"## ERRORS TO FIX\n```\n{err_text}\n```")

        if context.get("existing_content"):
            ec = context["existing_content"]
            if len(ec) > MAX_FILE_CHARS:
                ec = ec[:MAX_FILE_CHARS] + "\n... [truncated]"
            parts.append(f"## EXISTING FILE CONTENT\n```\n{ec}\n```")

        # ── Available skills ───────────────────────────────────────────
        if context.get("available_skills"):
            skills = context["available_skills"]
            skill_list = "\n".join(f"- **{s}**" for s in skills)
            parts.append(f"## AVAILABLE SKILLS\n{skill_list}")

        # ── Conversation summary ───────────────────────────────────────
        if context.get("conversation_summary"):
            parts.append(f"## CONVERSATION SUMMARY\n{context['conversation_summary']}")

        # ── Dependency file contents ───────────────────────────────────
        if context.get("dependency_file"):
            parts.append(f"## DEPENDENCY FILE\n```\n{context['dependency_file']}\n```")

        if context.get("scripts"):
            parts.append(f"## PROJECT SCRIPTS\n```\n{context['scripts']}\n```")

        if context.get("git_log"):
            parts.append(f"## RECENT GIT LOG\n```\n{context['git_log']}\n```")

        return "\n\n".join(parts)
