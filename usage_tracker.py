"""Live token usage tracking for the AI Dev Team."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from threading import Lock


@dataclass
class AgentUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    calls: int = 0


class UsageTracker:
    def __init__(self):
        self._usage = defaultdict(AgentUsage)
        self._lock = Lock()

    def record(
        self,
        agent: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        total_tokens: int = 0,
    ):
        with self._lock:
            usage = self._usage[agent]
            usage.input_tokens += input_tokens
            usage.output_tokens += output_tokens
            usage.total_tokens += total_tokens
            usage.calls += 1

    def reset(self):
        """Reset all usage counters for a new team run."""
        with self._lock:
            self._usage.clear()

    def get_all(self):
        with self._lock:
            return {
                agent: AgentUsage(
                    input_tokens=usage.input_tokens,
                    output_tokens=usage.output_tokens,
                    total_tokens=usage.total_tokens,
                    calls=usage.calls,
                )
                for agent, usage in self._usage.items()
            }

    def totals(self) -> AgentUsage:
        with self._lock:
            return AgentUsage(
                input_tokens=sum(u.input_tokens for u in self._usage.values()),
                output_tokens=sum(u.output_tokens for u in self._usage.values()),
                total_tokens=sum(u.total_tokens for u in self._usage.values()),
                calls=sum(u.calls for u in self._usage.values()),
            )


tracker = UsageTracker()
