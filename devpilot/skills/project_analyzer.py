from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, List

class ProjectAnalyzerSkill:
    """Deterministic skill to scan a workspace and extract structured ProjectContext."""
    
    def __init__(self, workspace_dir: Path):
        self.workspace_dir = workspace_dir

    def detect_language(self, files: List[str]) -> str:
        exts = [f.split('.')[-1] for f in files if '.' in f]
        ext_counts = {ext: exts.count(ext) for ext in set(exts)}
        
        if 'py' in ext_counts and ext_counts['py'] > 0: return "Python"
        if 'ts' in ext_counts or 'tsx' in ext_counts: return "TypeScript"
        if 'js' in ext_counts or 'jsx' in ext_counts: return "JavaScript"
        if 'go' in ext_counts: return "Go"
        if 'rs' in ext_counts: return "Rust"
        if 'java' in ext_counts: return "Java"
        
        return "Unknown"

    def detect_framework(self, files: List[str], package_json: Dict[str, Any] = None) -> str:
        if package_json:
            deps = {**package_json.get("dependencies", {}), **package_json.get("devDependencies", {})}
            if "next" in deps: return "Next.js"
            if "react" in deps: return "React"
            if "vue" in deps: return "Vue"
            if "express" in deps: return "Express"
            
        if "manage.py" in files or "requirements.txt" in files:
            reqs = ""
            try:
                reqs = (self.workspace_dir / "requirements.txt").read_text(encoding="utf-8")
            except Exception: pass
            if "django" in reqs.lower(): return "Django"
            if "fastapi" in reqs.lower(): return "FastAPI"
            if "flask" in reqs.lower(): return "Flask"

        return "Unknown"

    def run(self) -> Dict[str, Any]:
        """Execute the deterministic scan and return the context data."""
        
        # Scan files up to 2 levels deep
        all_files = []
        for path in self.workspace_dir.rglob("*"):
            if ".git" in path.parts or "node_modules" in path.parts or ".venv" in path.parts or "__pycache__" in path.parts:
                continue
            if path.is_file():
                try:
                    rel = path.relative_to(self.workspace_dir).as_posix()
                    all_files.append(rel)
                except ValueError:
                    pass
        
        # Read package.json if it exists
        package_json = {}
        pkg_path = self.workspace_dir / "package.json"
        if pkg_path.exists():
            try:
                package_json = json.loads(pkg_path.read_text(encoding="utf-8"))
            except Exception:
                pass
                
        # Read pyproject.toml if it exists
        pyproject = False
        if (self.workspace_dir / "pyproject.toml").exists():
            pyproject = True

        language = self.detect_language(all_files)
        framework = self.detect_framework(all_files, package_json)
        
        dependencies = []
        if package_json:
            dependencies = list(package_json.get("dependencies", {}).keys()) + list(package_json.get("devDependencies", {}).keys())
        elif (self.workspace_dir / "requirements.txt").exists():
            try:
                reqs = (self.workspace_dir / "requirements.txt").read_text(encoding="utf-8").splitlines()
                dependencies = [r.split('==')[0].strip() for r in reqs if r and not r.startswith('#')]
            except Exception:
                pass

        return {
            "project_name": self.workspace_dir.name,
            "language": language,
            "framework": framework,
            "package_manager": "npm" if (self.workspace_dir / "package-lock.json").exists() else ("yarn" if (self.workspace_dir / "yarn.lock").exists() else ("poetry" if (self.workspace_dir / "poetry.lock").exists() else "pip")),
            "testing_framework": "jest" if "jest" in dependencies else ("pytest" if "pytest" in dependencies else "Unknown"),
            "git_detected": (self.workspace_dir / ".git").exists(),
            "dependencies": dependencies,
            "existing_files": all_files,
        }
