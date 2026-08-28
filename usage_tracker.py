"""Live token, cost, and run-history tracking for the AI Dev Team."""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from team_config import get_config
from threading import Lock


# USD per 1 million tokens.
MODEL_PRICING = {
    "openai/gpt-oss-120b": {
        "input": 0.15,
        "output": 0.60,
    },
    "openai/gpt-oss-20b": {
        "input": 0.075,
        "output": 0.30,
    },
}


@dataclass
class AgentUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    calls: int = 0
    estimated_cost: float = 0.0


class UsageTracker:
    def __init__(self):
        self._usage = defaultdict(AgentUsage)
        self._models = {}
        self._lock = Lock()

    def reset(self):
        """Reset all usage counters for a new team run."""
        with self._lock:
            self._usage.clear()
            self._models.clear()

    def record(
        self,
        agent: str,
        model: str,
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

            pricing = MODEL_PRICING.get(model)

            if pricing:
                usage.estimated_cost += (
                    (input_tokens / 1_000_000) * pricing["input"]
                    + (output_tokens / 1_000_000) * pricing["output"]
                )

            self._models[agent] = model

    def get_all(self):
        with self._lock:
            return {
                agent: AgentUsage(
                    input_tokens=usage.input_tokens,
                    output_tokens=usage.output_tokens,
                    total_tokens=usage.total_tokens,
                    calls=usage.calls,
                    estimated_cost=usage.estimated_cost,
                )
                for agent, usage in self._usage.items()
            }

    def get_models(self):
        with self._lock:
            return dict(self._models)

    def totals(self) -> AgentUsage:
        with self._lock:
            return AgentUsage(
                input_tokens=sum(u.input_tokens for u in self._usage.values()),
                output_tokens=sum(u.output_tokens for u in self._usage.values()),
                total_tokens=sum(u.total_tokens for u in self._usage.values()),
                calls=sum(u.calls for u in self._usage.values()),
                estimated_cost=sum(
                    u.estimated_cost for u in self._usage.values()
                ),
            )

    def snapshot(self):
        usage = self.get_all()
        models = self.get_models()
        totals = self.totals()

        return {
            "agents": {
                agent: {
                    **asdict(data),
                    "model": models.get(agent),
                }
                for agent, data in usage.items()
            },
            "totals": asdict(totals),
        }

    def save_history(
        self,
        path: str | Path | None = None,
        metadata: dict | None = None,
    ):
        """Append this run's usage and build metadata to persistent history."""
        history_path = (
            Path(path)
            if path is not None
            else get_config().run_history_path
        )
        history_path.parent.mkdir(parents=True, exist_ok=True)

        if history_path.exists():
            try:
                history = json.loads(history_path.read_text())
            except (json.JSONDecodeError, OSError):
                history = []
        else:
            history = []

        totals = self.totals()

        run_number = len(history) + 1

        entry = {
            "run": run_number,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "usage": self.snapshot(),
            "total_tokens": totals.total_tokens,
            "estimated_cost": totals.estimated_cost,
        }

        # Metadata is intentionally additive so older history entries
        # remain completely valid and readable.
        if metadata:
            reserved = {
                "run",
                "timestamp",
                "usage",
                "total_tokens",
                "estimated_cost",
            }

            for key, value in metadata.items():
                if key not in reserved:
                    entry[key] = value

        history.append(entry)

        history_path.write_text(json.dumps(history, indent=2))

        return run_number


tracker = UsageTracker()
