"""
core/registry.py
================
Dynamic registries for Agents and Skills.
Allows discovering, enabling, and disabling capabilities without
hardcoding them into the orchestrator.
"""

from typing import Dict, Any, Optional

class AgentRegistry:
    def __init__(self):
        self._agents: Dict[str, Any] = {}
        self._enabled: Dict[str, bool] = {}

    def register(self, name: str, agent_instance: Any, enabled: bool = True):
        self._agents[name] = agent_instance
        self._enabled[name] = enabled

    def enable(self, name: str):
        if name in self._agents:
            self._enabled[name] = True

    def disable(self, name: str):
        if name in self._agents:
            self._enabled[name] = False

    def get(self, name: str) -> Optional[Any]:
        if self._enabled.get(name, False):
            return self._agents.get(name)
        return None
        
    def get_all_enabled(self) -> Dict[str, Any]:
        return {name: agent for name, agent in self._agents.items() if self._enabled.get(name, False)}
        
    def get_all(self) -> Dict[str, Any]:
        return self._agents.copy()

class SkillRegistry:
    def __init__(self):
        self._skills: Dict[str, Any] = {}
        self._enabled: Dict[str, bool] = {}

    def register(self, name: str, skill_instance: Any, enabled: bool = True):
        self._skills[name] = skill_instance
        self._enabled[name] = enabled

    def enable(self, name: str):
        if name in self._skills:
            self._enabled[name] = True

    def disable(self, name: str):
        if name in self._skills:
            self._enabled[name] = False

    def get(self, name: str) -> Optional[Any]:
        if self._enabled.get(name, False):
            return self._skills.get(name)
        return None

    def get_all_enabled(self) -> Dict[str, Any]:
        return {name: skill for name, skill in self._skills.items() if self._enabled.get(name, False)}

    def get_all(self) -> Dict[str, Any]:
        return self._skills.copy()
