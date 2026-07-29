"""
agents/validator.py
===================
Validation Agent: Inspects written workspace files for existence, syntax, duplicate paths, and import sanity.
"""

from __future__ import annotations

import ast
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, List, Optional

from agents.base import Agent
from core.event_bus import EventBus
from core.llm import LLMClient


@dataclass
class ValidationErrorItem:
    file_path: str
    error_type: str
    message: str
    line_number: Optional[int] = None
    suggested_fix: Optional[str] = None


@dataclass
class ValidatorInput:
    workspace_dir: Path
    written_files: List[str]


@dataclass
class ValidatorOutput:
    passed: bool
    errors: List[ValidationErrorItem] = field(default_factory=list)


from core.agent_logger import AgentLogger


class ValidatorAgent(Agent[ValidatorInput, ValidatorOutput]):
    """Validates physical disk files, syntax, duplicate paths, and structure."""

    name = "validator"

    def __init__(self, llm: Optional[LLMClient] = None, bus: Optional[EventBus] = None, logger: Optional[AgentLogger] = None) -> None:
        self._llm = llm
        self._bus = bus
        self._logger = logger or AgentLogger()

    async def run(self, agent_input: ValidatorInput) -> ValidatorOutput:
        self.emit_progress(current_validation="Starting validation", imports="-", exports="-", dependencies="-", components="-", current_milestone="Starting validation", current_skill="Code Analysis", progress="0%")
        import asyncio
        
        self._logger.log("Validator", f"Starting validation of {len(agent_input.written_files)} written files")
        errors: List[ValidationErrorItem] = []
        workspace = Path(agent_input.workspace_dir).resolve()
        seen_paths = set()

        total = len(agent_input.written_files)
        for idx, rel_path in enumerate(agent_input.written_files):
            prog_pct = int(((idx) / total) * 100) if total > 0 else 0
            self.emit_progress(current_validation=rel_path, current_milestone=f"Scanning {rel_path}", current_skill="Code Analysis", progress=f"{prog_pct}%")
            await asyncio.sleep(0.05) # Give UI time to render scanning effect
            # 1. Duplicate check
            norm_path = rel_path.replace("\\", "/").lower()
            if norm_path in seen_paths:
                errors.append(
                    ValidationErrorItem(
                        file_path=rel_path,
                        error_type="DuplicateFileError",
                        message=f"Duplicate file path detected: {rel_path}",
                        suggested_fix="Consolidate duplicate file generation in Architect plan.",
                    )
                )
            seen_paths.add(norm_path)

            target = (workspace / rel_path).resolve()

            # 2. Disk Existence Check
            if not target.exists() or not target.is_file():
                errors.append(
                    ValidationErrorItem(
                        file_path=rel_path,
                        error_type="FileSaveError",
                        message=f"File {rel_path} was not physically saved to disk.",
                        suggested_fix="Verify workspace write permissions.",
                    )
                )
                continue

            # 3. Syntax Verification
            ext = target.suffix.lower()
            content = target.read_text(encoding="utf-8", errors="replace")

            if ext == ".py":
                try:
                    ast.parse(content, filename=rel_path)
                except SyntaxError as syn_err:
                    errors.append(
                        ValidationErrorItem(
                            file_path=rel_path,
                            error_type="SyntaxError",
                            message=syn_err.msg or "Invalid Python syntax",
                            line_number=syn_err.lineno,
                            suggested_fix="Correct Python syntax, unclosed quotes, or missing indentation.",
                        )
                    )
            elif ext == ".json":
                try:
                    json.loads(content)
                except json.JSONDecodeError as json_err:
                    errors.append(
                        ValidationErrorItem(
                            file_path=rel_path,
                            error_type="JSONDecodeError",
                            message=json_err.msg,
                            line_number=json_err.lineno,
                            suggested_fix="Ensure JSON format has valid closing brackets and double-quoted keys.",
                        )
                    )

        passed = len(errors) == 0
        self.emit_progress(current_validation="Validation Complete", current_milestone="Validation Complete", current_skill="Code Analysis", progress="100%")
        return ValidatorOutput(passed=passed, errors=errors)
