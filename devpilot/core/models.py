from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


# ─────────────────────────────────────────────────────────────
# Planner Models
# ─────────────────────────────────────────────────────────────

class PlannerMilestone(BaseModel):
    id: int
    title: str
    description: str
    agent: str
    acceptance_criteria: List[str] = Field(default_factory=list)
    estimated_files: List[str] = Field(default_factory=list)
    depends_on: List[int] = Field(default_factory=list)

class PlannerOutput(BaseModel):
    status: str = Field(default="ready", description="ready | needs_clarification")
    project: str = Field(..., description="Short project name")
    project_type: str = Field(..., description="new_project | feature | bug_fix | refactor | documentation | deployment")
    complexity: str = Field(..., description="trivial | small | medium | large | enterprise")
    language: str = Field(..., description="Primary programming language")
    framework: Optional[str] = Field(None, description="Primary framework, or null")
    summary: str = Field(..., description="2-3 sentence executive summary")
    risks: List[str] = Field(default_factory=list)
    milestones: List[PlannerMilestone] = Field(default_factory=list)
    required_agents: List[str] = Field(default_factory=list)
    required_skills: List[str] = Field(default_factory=list)
    clarification_needed: List[str] = Field(default_factory=list)


# ─────────────────────────────────────────────────────────────
# Architect Models
# ─────────────────────────────────────────────────────────────

class FileBlueprint(BaseModel):
    path: str = Field(..., description="Relative file path from workspace root")
    purpose: str = Field(..., description="Precise one-sentence responsibility statement")
    action: str = Field(..., description="create | modify | delete")
    type: str = Field(default="code", description="code | test | config | docs")
    imports_from: List[str] = Field(default_factory=list)
    exported_symbols: List[str] = Field(default_factory=list)

class ArchitectureOutput(BaseModel):
    tech_stack: List[str] = Field(default_factory=list)
    architectural_pattern: str = Field(..., description="layered | mvc | service | event-driven | monolith | script")
    folders: List[str] = Field(default_factory=list)
    files: List[FileBlueprint] = Field(default_factory=list)
    new_dependencies: List[str] = Field(default_factory=list)
    testing_strategy: str = Field(default="unit", description="unit | integration | e2e | none")
    warnings: List[str] = Field(default_factory=list)


# ─────────────────────────────────────────────────────────────
# Coder Models
# ─────────────────────────────────────────────────────────────

class CodePatch(BaseModel):
    path: str = Field(..., description="Relative file path")
    action: str = Field(..., description="create | update | delete")
    content: str = Field(default="", description="Complete file content")

class CoderOutput(BaseModel):
    patches: List[CodePatch] = Field(default_factory=list)
    new_dependencies: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    summary: str = Field(default="", description="1-2 sentence implementation summary")


# ─────────────────────────────────────────────────────────────
# Reviewer Models
# ─────────────────────────────────────────────────────────────

class ReviewIssue(BaseModel):
    file: str
    line_hint: Optional[str] = None
    severity: str = Field(..., description="high | medium | low")
    category: str = Field(..., description="architecture | security | performance | error_handling | testing | documentation | code_quality | api_design")
    issue: str
    suggestion: str

class ReviewOutput(BaseModel):
    status: str = Field(default="reviewed", description="reviewed | insufficient_context")
    issues: List[ReviewIssue] = Field(default_factory=list)
    overall_quality: str = Field(..., description="excellent | good | needs_improvement | poor")
    summary: str = Field(..., description="2-3 sentence overall assessment")


# ─────────────────────────────────────────────────────────────
# GitHub Models
# ─────────────────────────────────────────────────────────────

class GitHubOutput(BaseModel):
    status: str = Field(default="ready", description="ready | error | nothing_to_commit")
    commit_message: str = Field(..., description="Full conventional commit message")
    git_add: List[str] = Field(default_factory=list, description="Files to stage")
    push_command: str = Field(default="", description="Full git push command")
    branch: str = Field(default="main")
    breaking_change: bool = Field(default=False)
    warnings: List[str] = Field(default_factory=list)
    summary: str = Field(default="")


# ─────────────────────────────────────────────────────────────
# Router Models
# ─────────────────────────────────────────────────────────────

class IntentRoute(BaseModel):
    intent: str = Field(..., description="'chat' or 'task'")
    pipeline_type: str = Field(..., description="'Project Creation', 'Bug Fix', 'Documentation', or 'Custom'")
    required_agents: List[str] = Field(..., description="Ordered list of agents to run")
