"""
core/session.py
===============
Manages the persistent session state for the interactive CLI.
Replaces the temporary ProjectMemory.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any
import json
from pathlib import Path

@dataclass
class SessionState:
    workspace_dir: str = ""
    model_name: str = ""
    history: List[Dict[str, Any]] = field(default_factory=list)
    enabled_agents: List[str] = field(default_factory=list)
    enabled_skills: List[str] = field(default_factory=list)
    generated_files: List[str] = field(default_factory=list)
    pending_tasks: List[str] = field(default_factory=list)
    completed_tasks: List[str] = field(default_factory=list)
    project_metadata: Dict[str, Any] = field(default_factory=dict)
    
class SessionManager:
    def __init__(self, session_file: Path):
        self.session_file = session_file
        self.state = SessionState()
        self.load()
        
    @property
    def active_session(self):
        return self
        
    def load(self):
        if self.session_file.exists():
            try:
                data = json.loads(self.session_file.read_text(encoding="utf-8"))
                self.state = SessionState(**data)
            except Exception:
                self.state = SessionState()
                
    def save(self):
        self.session_file.parent.mkdir(parents=True, exist_ok=True)
        self.session_file.write_text(json.dumps(asdict(self.state), indent=2), encoding="utf-8")
