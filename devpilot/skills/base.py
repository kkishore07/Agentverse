"""
skills/base.py
==============
Base interface for all DevPilot Skills.
Skills are tools that can be requested by Agents via structured output.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any

class SkillError(Exception):
    pass

class Skill(ABC):
    name: str = "base_skill"
    description: str = ""

    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the skill with the given arguments."""
        pass
