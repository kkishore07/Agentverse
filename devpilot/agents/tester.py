"""
agents/tester.py
================
Tester Agent: Runs project test suites (pytest, npm test, etc.) and captures test outcomes.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from agents.base import Agent
from core.event_bus import EventBus
from core.llm import LLMClient


@dataclass
class TesterInput:
    workspace_dir: Path


@dataclass
class TesterOutput:
    ran_tests: bool
    passed: bool
    command: str = ""
    stdout: str = ""
    stderr: str = ""
    duration_seconds: float = 0.0


from core.agent_logger import AgentLogger


class TesterAgent(Agent[TesterInput, TesterOutput]):
    """Executes automated tests in workspace and reports outcomes."""

    name = "tester"

    def __init__(self, llm: Optional[LLMClient] = None, bus: Optional[EventBus] = None, logger: Optional[AgentLogger] = None) -> None:
        self._llm = llm
        self._bus = bus
        self._logger = logger or AgentLogger()

    async def run(self, agent_input: TesterInput) -> TesterOutput:
        workspace = Path(agent_input.workspace_dir).resolve()
        self._logger.log("Tester", f"Detecting test runner in {workspace}")

        # Detect test runner
        cmd = None
        if (workspace / "pytest.ini").exists() or (workspace / "tests").exists() or any(workspace.glob("test_*.py")):
            cmd = "pytest"
        elif (workspace / "package.json").exists():
            cmd = "npm test"

        if not cmd:
            return TesterOutput(ran_tests=False, passed=True)

        start_t = time.time()
        try:
            self.emit_progress(current_command=cmd, current_test="-", passed=0, failed=0, execution_time="0.0s", current_milestone="Preparing tests", current_skill="Testing Framework", progress="0%")
            proc = await asyncio.create_subprocess_shell(
                cmd,
                cwd=str(workspace),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            passed_count = 0
            failed_count = 0
            stdout_chunks = []
            
            while True:
                line_b = await proc.stdout.readline()
                if not line_b:
                    break
                
                line = line_b.decode(errors="replace")
                stdout_chunks.append(line)
                
                # Simple parsing for Pytest or npm output
                if "PASSED" in line or "✓" in line:
                    passed_count += 1
                elif "FAILED" in line or "✖" in line:
                    failed_count += 1
                
                test_name = line.split(" ")[0] if len(line.strip()) > 3 else "-"
                
                self.emit_progress(
                    current_test=test_name[:20],
                    passed=passed_count,
                    failed=failed_count,
                    execution_time=f"{round(time.time() - start_t, 1)}s",
                    current_milestone=f"Running {cmd}",
                    current_skill="Testing Framework",
                    progress="50%" # Indeterminate while streaming
                )

            stderr_b = await proc.stderr.read()
            await proc.wait()
            
            duration = round(time.time() - start_t, 2)
            passed = proc.returncode == 0
            self.emit_progress(current_milestone="Testing Complete", current_skill="Testing Framework", progress="100%")
            return TesterOutput(
                ran_tests=True,
                passed=passed,
                command=cmd,
                stdout="".join(stdout_chunks),
                stderr=stderr_b.decode(errors="replace") if stderr_b else "",
                duration_seconds=duration,
            )
        except Exception as exc:
            return TesterOutput(
                ran_tests=True,
                passed=False,
                command=cmd or "test",
                stderr=str(exc),
                duration_seconds=0.0,
            )
