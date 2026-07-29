import subprocess
from pathlib import Path
from typing import List, Dict, Any

class GitSkill:
    """Deterministic skill to handle real git operations."""
    
    def __init__(self, workspace_dir: Path):
        self.workspace_dir = workspace_dir

    def _run_git(self, *args) -> str:
        try:
            result = subprocess.run(
                ["git"] + list(args),
                cwd=str(self.workspace_dir),
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            return e.stdout.strip() or e.stderr.strip()

    def get_status(self) -> Dict[str, Any]:
        """Returns the current git status as structured data."""
        if not (self.workspace_dir / ".git").exists():
            return {"is_git_repo": False}
            
        branch = self._run_git("branch", "--show-current")
        remote = self._run_git("remote", "get-url", "origin")
        status_raw = self._run_git("status", "--porcelain")
        
        modified = []
        new = []
        deleted = []
        
        for line in status_raw.splitlines():
            if not line: continue
            state, path = line[:2], line[3:]
            if "M" in state: modified.append(path)
            elif "??" in state or "A" in state: new.append(path)
            elif "D" in state: deleted.append(path)
            
        return {
            "is_git_repo": True,
            "branch": branch,
            "remote": remote,
            "modified_files": modified,
            "new_files": new,
            "deleted_files": deleted
        }

    def commit(self, message: str) -> bool:
        """Adds all changes and commits them."""
        self._run_git("add", ".")
        res = self._run_git("commit", "-m", message)
        return "nothing to commit" not in res.lower()
        
    def push(self) -> bool:
        """Pushes to the current branch."""
        res = self._run_git("push")
        return "error" not in res.lower()
