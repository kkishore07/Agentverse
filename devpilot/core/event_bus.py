"""
core/event_bus.py
=================
Event Bus for publishing and subscribing to events.
Extended with fine-grained transparency events for the live activity view.
"""
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Any
import asyncio


@dataclass
class Event:
    name: str
    data: Dict[str, Any] = field(default_factory=dict)


# All valid event names (for documentation purposes)

# Pipeline events
EVENT_PIPELINE_STARTED       = "PipelineStarted" # Pipeline type (e.g. 'Project Creation')
EVENT_PIPELINE_STAGE_CHANGED = "PipelineStageChanged" # active stage (e.g. 'Planner')

# Transparency events
EVENT_AGENT_STARTED      = "AgentStarted"
EVENT_AGENT_STEP         = "AgentStep"       # fine-grained agent step (checkmark item)
EVENT_AGENT_PROGRESS     = "AgentProgress"   # continuous real-time streaming updates
EVENT_AGENT_FINISHED     = "AgentFinished"
EVENT_THINKING           = "Thinking"        # reasoning display

# File transparency events
EVENT_FILE_READING       = "FileReading"     # 📖 Reading file.py
EVENT_FILE_CREATING      = "FileCreating"    # 📄 Creating file.py
EVENT_FILE_EDITING       = "FileEditing"     # ✏️  Editing file.py
EVENT_FILE_DELETING      = "FileDeleting"    # 🗑️  Deleting file.py
EVENT_CODE_STREAM        = "CodeStream"      # a chunk of generated code
EVENT_CODE_COMPLETE      = "CodeComplete"    # full file content ready
EVENT_DIFF_READY         = "DiffReady"       # diff for existing file
EVENT_FILE_CONFIRMED     = "FileConfirmed"   # ✓ file written, stats

# Chat events
EVENT_CHAT_TOKEN         = "ChatToken"       # streaming chat token
EVENT_CHAT_COMPLETE      = "ChatComplete"    # full response assembled

# Task lifecycle events
EVENT_TASK_STARTED       = "TaskStarted"
EVENT_TASK_COMPLETE      = "TaskComplete"    # final summary data
EVENT_ERROR              = "Error"
EVENT_WARNING            = "Warning"
EVENT_STATUS             = "Status"


class EventBus:
    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[Event], Any]]] = {}

    def subscribe(self, event_name: str, callback: Callable[[Event], Any]):
        if event_name not in self._subscribers:
            self._subscribers[event_name] = []
        self._subscribers[event_name].append(callback)

    def unsubscribe(self, event_name: str, callback: Callable[[Event], Any]):
        if event_name in self._subscribers and callback in self._subscribers[event_name]:
            self._subscribers[event_name].remove(callback)

    def subscribe_all(self, callback: Callable[[Event], Any]):
        """Subscribe to every event — useful for the UI bridge."""
        self._subscribers.setdefault("*", []).append(callback)

    def publish(self, event_name: str, **kwargs):
        event = Event(name=event_name, data=kwargs)
        for callback in self._subscribers.get(event_name, []):
            if asyncio.iscoroutinefunction(callback):
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.ensure_future(callback(event))
                    else:
                        loop.run_until_complete(callback(event))
                except RuntimeError:
                    pass
            else:
                callback(event)
        # wildcard subscribers
        for callback in self._subscribers.get("*", []):
            if not asyncio.iscoroutinefunction(callback):
                callback(event)
