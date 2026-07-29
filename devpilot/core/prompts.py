"""
core/prompts.py
================
All prompt templates live here, separated from agent execution logic.

Why separate: prompt wording is the thing you'll iterate on constantly
while tuning a small local model like qwen2.5-coder:3b. Keeping
templates out of agent classes means changing a prompt never risks
touching control flow, and it makes the prompts easy to diff/review on
their own.

Convention: every function here returns a `(system_prompt, user_prompt)`
tuple, matching the two arguments `LLMClient.generate()` accepts.
"""

from __future__ import annotations

import json


# ---------------------------------------------------------------------------
# Planner
# ---------------------------------------------------------------------------

PLANNER_SYSTEM = """You are a senior technical project planner.
You break a software project request into a short, ordered list of concrete
engineering tasks. You respond with ONLY valid JSON, no prose, no markdown
fences, no explanations."""


def planner_prompt(goal: str) -> tuple[str, str]:
    user = f"""Project request: "{goal}"

Return a JSON object with this EXACT shape:
{{
  "project": "<short project name>",
  "tasks": ["<task 1>", "<task 2>", "..."]
}}

Rules:
- 4 to 8 tasks, each a short concrete engineering step (not vague).
- Tasks should be ordered logically (setup first, then features, then tests/docs).
- Output ONLY the JSON object. No other text."""
    return PLANNER_SYSTEM, user


# ---------------------------------------------------------------------------
# Architect
# ---------------------------------------------------------------------------

ARCHITECT_SYSTEM = """You are a senior software architect.
Given a project plan, you design a minimal, sensible folder/file layout and
tech stack. You respond with ONLY valid JSON, no prose, no markdown fences."""


def architect_prompt(goal: str, tasks: list[str], max_files: int) -> tuple[str, str]:
    tasks_block = "\n".join(f"- {t}" for t in tasks)
    user = f"""Project: "{goal}"

Planned tasks:
{tasks_block}

Design the project structure. Return a JSON object with this EXACT shape:
{{
  "tech_stack": ["<library/framework>", "..."],
  "folders": ["<folder path>", "..."],
  "files": [
    {{"path": "<relative file path>", "purpose": "<one sentence: what this file does>", "type": "code"}},
    ...
  ]
}}

Rules:
- Include a "requirements.txt" or equivalent dependency file if the stack needs one.
- Include at least one test file under a "tests/" folder with "type": "test".
- Include exactly one "README.md" entry with "type": "docs".
- At most {max_files} files total.
- File paths must be relative (no leading slash, no "..").
- Output ONLY the JSON object. No other text."""
    return ARCHITECT_SYSTEM, user


# ---------------------------------------------------------------------------
# Code Generator
# ---------------------------------------------------------------------------

CODER_SYSTEM = """You are a senior software engineer writing production-quality
code. You write clean, correct, well-commented code with proper error handling
and imports. You respond with ONLY the raw file content -- no markdown code
fences, no explanations before or after, just the file's exact contents."""


def coder_prompt(
    goal: str,
    tech_stack: list[str],
    file_path: str,
    file_purpose: str,
    sibling_files: list[str],
) -> tuple[str, str]:
    stack_block = ", ".join(tech_stack) if tech_stack else "standard library"
    siblings_block = "\n".join(f"- {p}" for p in sibling_files) if sibling_files else "(none yet)"
    user = f"""Project: "{goal}"
Tech stack: {stack_block}

You are generating ONE file: "{file_path}"
Purpose of this file: {file_purpose}

Other files in this project (for import/reference consistency):
{siblings_block}

Requirements:
- Write complete, runnable content for "{file_path}" ONLY.
- Include necessary imports.
- Add concise comments for non-obvious logic.
- Include reasonable error handling where relevant (e.g. I/O, request handlers).
- Use clear naming and follow idiomatic conventions for the file's language.
- If this is a config/requirements/markdown file, produce appropriate content
  for that format instead of Python code.
- Output ONLY the raw file content. No markdown fences, no commentary."""
    return CODER_SYSTEM, user


# ---------------------------------------------------------------------------
# Test Generator
# ---------------------------------------------------------------------------

TESTER_SYSTEM = """You are a senior test engineer. You write meaningful pytest
tests that actually exercise the given source code's behavior, including at
least one edge case. You respond with ONLY the raw test file content -- no
markdown fences, no explanations."""


def tester_prompt(goal: str, source_file_path: str, source_content: str, test_file_path: str) -> tuple[str, str]:
    user = f"""Project: "{goal}"

Write pytest tests for the following source file.

Source file path: {source_file_path}
Source file content:
---
{source_content}
---

Write the complete content for the test file: "{test_file_path}"

Requirements:
- Use pytest conventions (test_ function names, plain asserts).
- Cover at least one happy path and one edge/error case.
- Import the module under test using a path consistent with the project layout.
- Output ONLY the raw test file content. No markdown fences, no commentary."""
    return TESTER_SYSTEM, user


# ---------------------------------------------------------------------------
# Documentation
# ---------------------------------------------------------------------------

DOCS_SYSTEM = """You are a technical writer producing a clear, professional
README for a software project. You respond with ONLY the raw markdown
content -- no code fences wrapping the whole thing, no meta-commentary."""


def docs_prompt(goal: str, tech_stack: list[str], files: list[dict]) -> tuple[str, str]:
    files_block = "\n".join(f"- `{f['path']}` -- {f.get('purpose', '')}" for f in files)
    stack_block = ", ".join(tech_stack) if tech_stack else "Python standard library"
    user = f"""Project: "{goal}"
Tech stack: {stack_block}

Files in this project:
{files_block}

Write a README.md with these sections: Title, short description,
Tech Stack, Installation, Usage, Project Structure (briefly explain each
folder/file above), and Running Tests.

Output ONLY the raw markdown content."""
    return DOCS_SYSTEM, user


# ---------------------------------------------------------------------------
# Explain / Improve (used by `devpilot explain` / `devpilot improve`)
# ---------------------------------------------------------------------------

EXPLAIN_SYSTEM = """You are a senior engineer explaining code to a teammate.
Be concise, accurate, and structured."""


def explain_prompt(file_path: str, content: str) -> tuple[str, str]:
    user = f"""Explain what this file does.

File: {file_path}
Content:
---
{content}
---

Give: (1) a 2-3 sentence summary, (2) key functions/classes and their role,
(3) any notable risks or edge cases."""
    return EXPLAIN_SYSTEM, user


IMPROVE_SYSTEM = """You are a senior engineer performing a focused code
review and improvement pass. You respond with ONLY the improved raw file
content -- no markdown fences, no commentary -- unless no changes are
warranted, in which case return the original content unchanged."""


def improve_prompt(file_path: str, content: str) -> tuple[str, str]:
    user = f"""Improve this file: readability, correctness, error handling,
and idiomatic style. Preserve its existing behavior/interface.

File: {file_path}
Content:
---
{content}
---

Output ONLY the improved raw file content."""
    return IMPROVE_SYSTEM, user

# ---------------------------------------------------------------------------
# Fixer Agent
# ---------------------------------------------------------------------------

FIXER_SYSTEM = """You are a senior software engineer specialized in debugging and fixing code.
You are given a file with errors (syntax errors, failed tests, validation issues) and you must fix it.
You respond with ONLY the corrected raw file content -- no markdown fences, no explanations."""

def fixer_prompt(file_path: str, content: str, errors: list[str]) -> tuple[str, str]:
    errors_block = "\n".join(f"- {err}" for err in errors)
    user = f"""Fix the errors in this file.

File: {file_path}
Errors:
{errors_block}

Current Content:
---
{content}
---

Output ONLY the completely fixed raw file content. Do not include markdown fences or any other text."""
    return FIXER_SYSTEM, user

# ---------------------------------------------------------------------------
# Reviewer Agent
# ---------------------------------------------------------------------------

REVIEWER_SYSTEM = """You are a Staff Software Engineer doing a rigorous code review.
You evaluate code for security, performance, idiomatic style, and maintainability.
You respond with a structured JSON array of issues and recommendations, NO prose."""

def reviewer_prompt(goal: str, files: list[dict[str, str]]) -> tuple[str, str]:
    # files is a list of dicts with 'path' and 'content'
    files_block = "\n".join(f"--- {f['path']} ---\n{f['content']}\n" for f in files)
    user = f"""Project Goal: "{goal}"

Review the following files:
{files_block}

Return a JSON array of objects with this EXACT shape (return an empty array [] if no issues):
[
  {{
    "file": "<file path>",
    "severity": "<high|medium|low>",
    "issue": "<concise description of the problem>",
    "suggestion": "<concise suggestion to fix>"
  }}
]

Output ONLY the JSON array. No other text."""
    return REVIEWER_SYSTEM, user

# ---------------------------------------------------------------------------
# GitHub Agent
# ---------------------------------------------------------------------------

GITHUB_SYSTEM = """You are an automated Git assistant.
Given a summary of changes, you write a concise, conventional git commit message.
You respond with ONLY the commit message text (subject and optional body), nothing else."""

def github_prompt(goal: str, changed_files: list[str], diff_summary: str = "") -> tuple[str, str]:
    files_block = ", ".join(changed_files)
    user = f"""Generate a conventional commit message for these changes.

Project Goal: "{goal}"
Changed files: {files_block}
Diff Summary: {diff_summary}

Format:
<type>(<optional scope>): <subject>

<optional body>

Output ONLY the commit message. No markdown fences, no quotes."""
    return GITHUB_SYSTEM, user
