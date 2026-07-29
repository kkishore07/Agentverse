"""
workspace/manager.py
====================
WorkspaceDetector: Analyzes the current workspace directory for project information.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict


class WorkspaceDetector:
    """Detects project details such as language, framework, git status, and file count."""

    def __init__(self, workspace_dir: str | Path = ".") -> None:
        self.workspace_dir = Path(workspace_dir).resolve()

    def detect(self) -> Dict[str, Any]:
        if not self.workspace_dir.exists():
            return {
                "project_name": self.workspace_dir.name,
                "language": "Unknown",
                "framework": "None",
                "file_count": 0,
                "git_detected": False,
                "git_branch": "",
            }

        files = []
        try:
            for root, dirs, filenames in os.walk(self.workspace_dir):
                # Skip hidden dirs like .git, .venv, __pycache__, etc.
                dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__pycache__"]
                for f in filenames:
                    files.append(Path(root) / f)
        except Exception:
            pass

        file_count = len(files)
        git_dir = self.workspace_dir / ".git"
        git_detected = git_dir.exists() and git_dir.is_dir()
        git_branch = ""

        if git_detected:
            head_file = git_dir / "HEAD"
            if head_file.exists():
                try:
                    content = head_file.read_text().strip()
                    if content.startswith("ref: refs/heads/"):
                        git_branch = content.replace("ref: refs/heads/", "")
                    else:
                        git_branch = content[:7]
                except Exception:
                    git_branch = "main"

        # Simple Language & framework detection
        extensions = [f.suffix.lower() for f in files]
        lang = "Unknown"
        if ".py" in extensions:
            lang = "Python"
        elif ".ts" in extensions or ".tsx" in extensions:
            lang = "TypeScript"
        elif ".js" in extensions or ".jsx" in extensions:
            lang = "JavaScript"
        elif ".go" in extensions:
            lang = "Go"
        elif ".rs" in extensions:
            lang = "Rust"
        elif ".java" in extensions:
            lang = "Java"

        framework = "None"
        file_names = [f.name.lower() for f in files]
        if "package.json" in file_names:
            framework = "Node.js"
        elif "pyproject.toml" in file_names or "requirements.txt" in file_names:
            framework = "Python App"

        return {
            "project_name": self.workspace_dir.name,
            "language": lang,
            "framework": framework,
            "file_count": file_count,
            "git_detected": git_detected,
            "git_branch": git_branch,
        }
