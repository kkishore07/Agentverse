import ast
import json
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional

class ASTValidatorSkill:
    """Validates files strictly using AST, JSON parsers, and Yaml parsers (No LLM)."""
    
    def __init__(self, workspace_dir: Path):
        self.workspace_dir = workspace_dir

    def validate(self, written_files: List[str]) -> List[Dict[str, Any]]:
        errors = []
        seen_paths = set()

        for rel_path in written_files:
            norm_path = rel_path.replace("\\", "/").lower()
            if norm_path in seen_paths:
                errors.append({
                    "file_path": rel_path,
                    "error_type": "DuplicateFileError",
                    "message": f"Duplicate file path detected: {rel_path}",
                    "suggested_fix": "Consolidate duplicate file generation."
                })
            seen_paths.add(norm_path)

            target = (self.workspace_dir / rel_path).resolve()
            if not target.exists() or not target.is_file():
                errors.append({
                    "file_path": rel_path,
                    "error_type": "FileSaveError",
                    "message": f"File {rel_path} was not saved.",
                    "suggested_fix": "Verify write permissions."
                })
                continue

            ext = target.suffix.lower()
            content = target.read_text(encoding="utf-8", errors="replace")

            if ext == ".py":
                try:
                    ast.parse(content, filename=rel_path)
                except SyntaxError as syn_err:
                    errors.append({
                        "file_path": rel_path,
                        "error_type": "SyntaxError",
                        "message": syn_err.msg or "Invalid Python syntax",
                        "line_number": syn_err.lineno,
                        "suggested_fix": "Correct Python syntax, unclosed quotes, or missing indentation."
                    })
            elif ext == ".json":
                try:
                    json.loads(content)
                except json.JSONDecodeError as json_err:
                    errors.append({
                        "file_path": rel_path,
                        "error_type": "JSONDecodeError",
                        "message": json_err.msg,
                        "line_number": json_err.lineno,
                        "suggested_fix": "Ensure JSON format has valid closing brackets and double-quoted keys."
                    })
            elif ext in (".yml", ".yaml"):
                try:
                    yaml.safe_load(content)
                except Exception as yaml_err:
                    errors.append({
                        "file_path": rel_path,
                        "error_type": "YAMLError",
                        "message": str(yaml_err),
                        "suggested_fix": "Ensure valid YAML syntax (e.g. indentation)."
                    })
                    
        return errors
