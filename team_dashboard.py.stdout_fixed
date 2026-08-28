"""Live terminal dashboard for the AI Dev Team."""

from __future__ import annotations

import os
import time
from threading import Lock, Thread

from team_events import TeamEvent, events
from usage_tracker import tracker


AGENTS = [
    "Researcher",
    "Architect",
    "Developer",
    "Reviewer",
    "Security",
    "Tester",
    "Debugger",
]

ICONS = {
    "Researcher": "🔎",
    "Architect": "🏗️",
    "Developer": "💻",
    "Reviewer": "🔍",
    "Security": "🔐",
    "Tester": "🧪",
    "Debugger": "🐛",
}


class Dashboard:
    def __init__(self):
        self._lock = Lock()
        self.running = False
        self.current_agent = None
        self.status = {agent: "WAITING" for agent in AGENTS}
        self.messages = {agent: "" for agent in AGENTS}
        self.activity = []
        self.start_time = None
        self.run_number = None
        self._refresh_thread = None
        self._stop_refresh = False
        self._alternate_screen = False

        events.subscribe(self.handle_event)

    def start(self, run_number=None):
        with self._lock:
            self.running = True
            self.start_time = time.time()
            self.run_number = run_number
            self.activity = []
            self._stop_refresh = False

        # Enter the terminal's alternate screen so the live dashboard
        # has its own screen and never floods the normal terminal history.
        if not self._alternate_screen:
            print("\033[?1049h\033[H", end="", flush=True)
            self._alternate_screen = True

        self.render()

        if self._refresh_thread is None or not self._refresh_thread.is_alive():
            self._refresh_thread = Thread(
                target=self._refresh_loop,
                daemon=True,
            )
            self._refresh_thread.start()

    def stop(self):
        with self._lock:
            self.running = False
            self.current_agent = None
            self._stop_refresh = True

        if self._refresh_thread is not None:
            self._refresh_thread.join(timeout=1.0)
            self._refresh_thread = None

        self.render()

        # Return to the normal terminal screen after the team finishes.
        if self._alternate_screen:
            print("\033[?1049l", end="", flush=True)
            self._alternate_screen = False

    def _refresh_loop(self):
        while True:
            with self._lock:
                if self._stop_refresh:
                    break

            time.sleep(1.0)

            with self._lock:
                if self._stop_refresh:
                    break

            self.render()

    def handle_event(self, event: TeamEvent):
        with self._lock:
            if event.agent in self.status:
                if event.event_type == "AGENT_STARTED":
                    self.status[event.agent] = "WORKING"
                    self.current_agent = event.agent
                    self.messages[event.agent] = event.message

                elif event.event_type == "AGENT_COMPLETED":
                    self.status[event.agent] = "DONE"
                    self.messages[event.agent] = event.message

                elif event.event_type == "AGENT_FAILED":
                    self.status[event.agent] = "FAILED"
                    self.messages[event.agent] = event.message

            if event.agent and event.message:
                timestamp = event.timestamp[11:19] if len(event.timestamp) >= 19 else event.timestamp
                icon = ICONS.get(event.agent, "🤖")

                self.activity.append(
                    (timestamp, icon, event.agent, event.message)
                )

                self.activity = self.activity[-8:]

            elif event.event_type == "TEAM_LOG" and event.message:
                timestamp = event.timestamp[11:19] if len(event.timestamp) >= 19 else event.timestamp

                self.activity.append(
                    (timestamp, "ℹ️", "Team", event.message)
                )

                self.activity = self.activity[-8:]

            if event.event_type == "TEAM_STARTED":
                self.running = True

            elif event.event_type == "TEAM_COMPLETED":
                self.running = False
                self.current_agent = None

        # Rendering is intentionally controlled by the dashboard
        # refresh mechanism instead of every individual event.
        # This prevents the terminal from being cleared and redrawn
        # hundreds of times during a team run.

    def _format_time(self):
        if self.start_time is None:
            return "00:00:00"

        elapsed = int(time.time() - self.start_time)

        hours, remainder = divmod(elapsed, 3600)
        minutes, seconds = divmod(remainder, 60)

        return f"{hours:02}:{minutes:02}:{seconds:02}"

    def _status_symbol(self, status):
        return {
            "WAITING": "○",
            "WORKING": "●",
            "DONE": "✓",
            "FAILED": "✗",
        }.get(status, "?")

    def render(self):
        if not self.running and self.start_time is None:
            return

        with self._lock:
            statuses = dict(self.status)
            current = self.current_agent
            messages = dict(self.messages)

        usage = tracker.get_all()
        totals = tracker.totals()
        models = tracker.get_models()

        # Return to the top-left of the dashboard screen.
        print("\033[H", end="")

        print(
            "╭────────────────────────────────────────────────────────────╮"
        )

        run_text = (
            f"RUN #{self.run_number}"
            if self.run_number is not None
            else "AI DEV TEAM"
        )

        print(
            f"│ 🤖 AI DEV TEAM                         "
            f"{run_text:<10} {self._format_time()} │"
        )

        print(
            "├────────────────────────────────────────────────────────────┤"
        )
        print("│ AGENTS                                                     │")
        print("│                                                            │")

        for agent in AGENTS:
            status = statuses[agent]
            symbol = self._status_symbol(status)
            icon = ICONS[agent]

            data = usage.get(agent)

            if data:
                tokens = f"{data.total_tokens:,}"
                cost = f"${data.estimated_cost:.6f}"
            else:
                tokens = "0"
                cost = "$0.000000"

            print(
                f"│ {icon} {agent:<12} "
                f"{symbol} {status:<8} "
                f"{tokens:>10} tok  {cost:>10} │"
            )

        print(
            "├────────────────────────────────────────────────────────────┤"
        )

        print("│ ACTIVITY                                                    │")

        if self.activity:
            for timestamp, icon, agent, message in self.activity:
                text = f"{timestamp}  {icon} {agent:<11} {message}"
                print(f"│ {text[:58]:<58} │")
        else:
            print("│ No activity yet.                                           │")

        print("│                                                            │")

        print("│ CURRENT                                                    │")
        print("│                                                            │")

        if current:
            icon = ICONS.get(current, "🤖")
            message = messages.get(current) or "Working..."

            print(
                f"│ {icon} {current}                                        │"
            )
            print(f"│ {message[:56]:<56} │")
        else:
            print("│ No agent currently generating.                            │")

        print("│                                                            │")

        print(
            "├────────────────────────────────────────────────────────────┤"
        )
        print("│ USAGE                                                      │")
        print("│                                                            │")

        print(
            f"│ Total tokens   {totals.total_tokens:>10,}     "
            f"API calls   {totals.calls:>4}                   │"
        )

        print(
            f"│ Input tokens   {totals.input_tokens:>10,}     "
            f"Output      {totals.output_tokens:>10,}       │"
        )

        print(
            f"│ Estimated cost ${totals.estimated_cost:>10.6f}                     │"
        )

        print(
            "╰────────────────────────────────────────────────────────────╯"
        )



dashboard = Dashboard()
