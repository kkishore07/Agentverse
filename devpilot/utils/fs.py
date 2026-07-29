"""
utils/fs.py
===========
Filesystem helpers shared by the Project Writer (and CLI commands like
`explain`/`improve` that read generated files back).

Centralizing path-safety logic here prevents an LLM-suggested file path
like "../../etc/passwd" or "/etc/cron.d/x" from ever being written to
outside the intended project directory.
"""

from __future__ import annotations

from pathlib import Path


class UnsafePathError(Exception):
    """Raised when a candidate path would escape the project root."""


def safe_join(root: Path, relative_path: str) -> Path:
    """Join `relative_path` onto `root`, guaranteeing the result stays
    inside `root`.

    Args:
        root: The trusted base directory (a project's root folder).
        relative_path: A path suggested by the Architect/Coder agent --
            untrusted, since it originates from LLM output.

    Returns:
        A resolved, safe absolute Path inside `root`.

    Raises:
        UnsafePathError: if the resolved path escapes `root`.
    """
    candidate = (root / relative_path.lstrip("/\\")).resolve()
    root_resolved = root.resolve()
    if root_resolved not in candidate.parents and candidate != root_resolved:
        raise UnsafePathError(f"Path '{relative_path}' resolves outside project root '{root}'.")
    return candidate


def write_text_file(root: Path, relative_path: str, content: str) -> Path:
    """Safely write `content` to `relative_path` under `root`, creating
    parent directories as needed."""
    target = safe_join(root, relative_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return target


def slugify(text: str, max_length: int = 40) -> str:
    """Turn a free-form project description into a filesystem-safe slug
    for the workspace directory name, e.g. 'Build a FastAPI Todo App'
    -> 'build-a-fastapi-todo-app'."""
    import re

    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:max_length].rstrip("-") or "project"
