"""
agents/reviewer.py
==================
Reviewer Agent that evaluates code for security, performance,
idiomatic style, and maintainability.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any
from agents.base import Agent, AgentError
from core.prompts import reviewer_prompt


@dataclass(frozen=True)
class ReviewerInput:
    goal: str
    files: list[dict[str, str]]  # list of {"path": "...", "content": "..."}


@dataclass(frozen=True)
class ReviewIssue:
    file: str
    severity: str
    issue: str
    suggestion: str


@dataclass(frozen=True)
class ReviewerOutput:
    issues: list[ReviewIssue] = field(default_factory=list)


class ReviewerAgent(Agent[ReviewerInput, ReviewerOutput]):
    """Analyzes a set of files and returns structured review issues."""

    name = "reviewer"

    async def run(self, agent_input: ReviewerInput) -> ReviewerOutput:
        self.emit_progress(current_file_under_review="Scanning...", issues_found=0, suggestions="-", current_milestone="Reviewing workspace", current_skill="Static Analysis", progress="0%")
        
        system, user = reviewer_prompt(
            goal=agent_input.goal,
            files=agent_input.files,
        )
        
        full_text = ""
        try:
            stream = self._llm.stream(user, system=system)
            async for chunk in stream:
                full_text += chunk
                self.emit_progress(llm_token=chunk)
        except Exception as e:
            raise AgentError(f"Reviewer: LLM stream failed: {e}")
        
        try:
            # We expect a JSON array of issues
            from utils.json_utils import extract_json
            raw_issues = extract_json(full_text)
            
            issues = []
            if isinstance(raw_issues, list):
                for iss in raw_issues:
                    if isinstance(iss, dict) and "file" in iss and "issue" in iss:
                        issues.append(ReviewIssue(
                            file=iss.get("file", ""),
                            severity=iss.get("severity", "medium"),
                            issue=iss.get("issue", ""),
                            suggestion=iss.get("suggestion", "")
                        ))
            
            self.emit_progress(current_milestone=f"Found {len(issues)} issues", current_skill="Static Analysis", progress="100%", issues_found=len(issues))
            return ReviewerOutput(issues=issues)
        except json.JSONDecodeError as e:
            raise AgentError(f"ReviewerAgent failed to parse JSON output: {e}\nRaw output: {response.text}")
