import asyncio
import os
import subprocess
from pathlib import Path
from typing import Dict, Any

class TesterSkill:
    """Detects testing frameworks and streams execution output."""
    
    def __init__(self, workspace_dir: Path, bus=None):
        self.workspace_dir = workspace_dir
        self.bus = bus

    def detect_command(self, context: dict[str, Any]) -> str:
        """Use the enriched project context to find the best test command."""
        framework = context.get("testing_framework", "Unknown")
        pm = context.get("package_manager", "npm")
        
        if framework == "jest":
            return f"{pm} test"
        if framework == "pytest":
            return "pytest"
        if context.get("language") == "Go":
            return "go test ./..."
        if context.get("language") == "Rust":
            return "cargo test"
        if context.get("language") == "Python":
            return "python -m unittest discover"
            
        return ""

    async def run_tests(self, context: dict[str, Any]) -> Dict[str, Any]:
        command = self.detect_command(context)
        if not command:
            return {"passed": True, "output": "No test framework detected.", "skipped": True}

        from core.event_bus import EVENT_AGENT_STEP
        if self.bus:
            self.bus.publish(EVENT_AGENT_STEP, agent_name="Tester", step=f"Running command: {command}")

        # Stream terminal output
        process = await asyncio.create_subprocess_shell(
            command,
            cwd=str(self.workspace_dir),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT
        )

        output_lines = []
        while True:
            line = await process.stdout.readline()
            if not line:
                break
            decoded_line = line.decode('utf-8', errors='replace').rstrip()
            output_lines.append(decoded_line)
            if self.bus:
                # We can emit it as a log step to make the TUI look cool
                self.bus.publish(EVENT_AGENT_STEP, agent_name="Tester", step=decoded_line[:80])

        await process.wait()
        passed = (process.returncode == 0)
        
        return {
            "passed": passed,
            "output": "\n".join(output_lines),
            "command": command,
            "skipped": False
        }
