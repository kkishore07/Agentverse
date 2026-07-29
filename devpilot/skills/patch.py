import os
import difflib
from pathlib import Path

class PatchSkill:
    """Applies code patches to existing files or creates new ones."""
    
    def __init__(self, workspace_dir: Path):
        self.workspace_dir = workspace_dir

    def create_file(self, rel_path: str, content: str) -> bool:
        """Create a new file with the given content."""
        target_path = self.workspace_dir / rel_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content, encoding="utf-8")
        return True

    def delete_file(self, rel_path: str) -> bool:
        """Delete an existing file."""
        target_path = self.workspace_dir / rel_path
        if target_path.exists():
            target_path.unlink()
            return True
        return False

    def update_file(self, rel_path: str, patch_content: str) -> str:
        """Update a file. If patch_content is a unified diff, apply it. Otherwise, rewrite the file."""
        target_path = self.workspace_dir / rel_path
        if not target_path.exists():
            return self.create_file(rel_path, patch_content)

        # For now, we will assume the LLM generates the full updated content.
        # Generating valid unified diffs is notoriously hard for LLMs. 
        # In a real IDE, we'd use line replacements or a smart merge.
        # We will write the full content provided.
        target_path.write_text(patch_content, encoding="utf-8")
        
        return "Updated successfully."

    def generate_diff(self, original: str, updated: str) -> str:
        """Helper to generate unified diff strings for the UI to display before saving."""
        diff = difflib.unified_diff(
            original.splitlines(), 
            updated.splitlines(), 
            fromfile="Original", 
            tofile="Updated", 
            lineterm=""
        )
        return "\n".join(diff)
