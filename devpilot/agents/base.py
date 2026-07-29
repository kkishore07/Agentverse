"""
agents/base.py
==============
Base agent interface.
"""
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Any
from core.llm import LLMClient
from core.event_bus import EventBus

InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")

class AgentError(Exception):
    pass

class Agent(ABC, Generic[InputT, OutputT]):
    name: str = "agent"

    def __init__(self, llm: LLMClient, bus: EventBus):
        self._llm = llm
        self._bus = bus

    def emit_progress(self, **data: Any) -> None:
        from core.event_bus import EVENT_AGENT_PROGRESS
        self._bus.publish(EVENT_AGENT_PROGRESS, agent_name=self.name, **data)

    @abstractmethod
    async def run(self, agent_input: InputT) -> OutputT:
        raise NotImplementedError
