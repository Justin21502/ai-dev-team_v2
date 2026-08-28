"""Lightweight event bus for the AI Dev Team."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Lock
from typing import Callable, Any


@dataclass
class TeamEvent:
    event_type: str
    agent: str | None = None
    message: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class EventBus:
    """Tiny thread-safe event dispatcher."""

    def __init__(self):
        self._listeners: list[Callable[[TeamEvent], None]] = []
        self._lock = Lock()

    def subscribe(self, listener: Callable[[TeamEvent], None]):
        with self._lock:
            self._listeners.append(listener)

    def emit(
        self,
        event_type: str,
        agent: str | None = None,
        message: str = "",
        **data,
    ):
        event = TeamEvent(
            event_type=event_type,
            agent=agent,
            message=message,
            data=data,
        )

        with self._lock:
            listeners = list(self._listeners)

        for listener in listeners:
            try:
                listener(event)
            except Exception:
                # UI failures must never kill the AI team.
                pass


events = EventBus()
