"""
skills/terminal.py
==================
Allows running shell commands safely.
"""
import asyncio
from typing import Dict, Any
from pathlib import Path
from .base import Skill, SkillError

class TerminalSkill(Skill):
    name = "terminal"
    description = "Execute shell commands in the workspace."
    
    def __init__(self, workspace_dir: Path):
        self.workspace_dir = workspace_dir
        
    async def execute(self, command: str) -> Dict[str, Any]:
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(self.workspace_dir)
        )
        stdout, stderr = await process.communicate()
        
        return {
            "stdout": stdout.decode("utf-8"),
            "stderr": stderr.decode("utf-8"),
            "exit_code": process.returncode
        }
