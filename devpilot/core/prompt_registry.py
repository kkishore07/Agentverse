from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class PromptMetadata:
    name: str
    version: str
    author: str
    description: str
    supported_models: List[str]
    required_context: List[str]
    required_skills: List[str]
    output_schema: str
    maximum_tokens: int

class PromptRegistry:
    """Stores and validates prompt metadata configurations."""
    
    _registry: Dict[str, PromptMetadata] = {}
    
    @classmethod
    def register(cls, metadata: PromptMetadata):
        cls._registry[metadata.name] = metadata
        
    @classmethod
    def get(cls, name: str) -> Optional[PromptMetadata]:
        return cls._registry.get(name)
        
    @classmethod
    def validate_context(cls, name: str, context: Dict[str, Any]) -> None:
        """Validates that the provided context satisfies the prompt's requirements."""
        meta = cls.get(name)
        if not meta:
            raise ValueError(f"Prompt metadata not found for '{name}'")
            
        for req in meta.required_context:
            if req not in context:
                raise ValueError(f"Missing required context '{req}' for prompt '{name}'")

# Pre-registering standard devpilot prompts
PromptRegistry.register(PromptMetadata(
    name="planner",
    version="2.0",
    author="devpilot",
    description="Principal Engineering Manager for scoping and planning.",
    supported_models=["qwen2.5-coder", "qwen3", "gpt-4"],
    required_context=["goal"],
    required_skills=[],
    output_schema="PlannerOutput",
    maximum_tokens=4096
))

PromptRegistry.register(PromptMetadata(
    name="architect",
    version="2.0",
    author="devpilot",
    description="Principal Software Architect for project structure.",
    supported_models=["qwen2.5-coder", "qwen3", "gpt-4"],
    required_context=["goal", "project_context", "tasks"],
    required_skills=[],
    output_schema="ArchitectureOutput",
    maximum_tokens=8192
))

PromptRegistry.register(PromptMetadata(
    name="coder",
    version="2.0",
    author="devpilot",
    description="Senior Software Engineer for implementing logic.",
    supported_models=["qwen2.5-coder", "qwen3", "gpt-4"],
    required_context=["goal", "files", "project_context"],
    required_skills=["patch"],
    output_schema="CoderOutput",
    maximum_tokens=8192
))

PromptRegistry.register(PromptMetadata(
    name="fixer",
    version="2.0",
    author="devpilot",
    description="Automatic Repair Engineer for fixing test/validation errors.",
    supported_models=["qwen2.5-coder", "qwen3", "gpt-4"],
    required_context=["errors", "existing_content"],
    required_skills=["patch"],
    output_schema="CoderOutput",
    maximum_tokens=8192
))

PromptRegistry.register(PromptMetadata(
    name="reviewer",
    version="2.0",
    author="devpilot",
    description="Principal Engineer for code review.",
    supported_models=["qwen2.5-coder", "qwen3", "gpt-4"],
    required_context=["goal", "files"],
    required_skills=[],
    output_schema="ReviewOutput",
    maximum_tokens=8192
))

PromptRegistry.register(PromptMetadata(
    name="docs",
    version="2.0",
    author="devpilot",
    description="Senior Technical Writer for documentation.",
    supported_models=["qwen2.5-coder", "qwen3", "gpt-4"],
    required_context=["goal", "project_context", "architecture"],
    required_skills=[],
    output_schema="CoderOutput",
    maximum_tokens=8192
))

PromptRegistry.register(PromptMetadata(
    name="github",
    version="2.0",
    author="devpilot",
    description="Staff DevOps Engineer for git operations.",
    supported_models=["qwen2.5-coder", "qwen3", "gpt-4"],
    required_context=["goal", "diff_summary"],
    required_skills=["git"],
    output_schema="GitHubOutput",
    maximum_tokens=4096
))
