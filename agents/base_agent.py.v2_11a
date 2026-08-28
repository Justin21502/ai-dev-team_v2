from llm_client import chat
from team_events import events


class Agent:
    """A single team member: a name, role/system prompt, and conversation memory."""

    def __init__(
        self,
        name: str,
        role_prompt: str,
        model: str | None = None,
        temperature: float = 0.3,
    ):
        self.name = name
        self.role_prompt = role_prompt
        self.model = model
        self.temperature = temperature
        self.history = []

    def say(self, message: str, extra_context: str = "") -> str:
        events.emit(
            "AGENT_STARTED",
            agent=self.name,
            message="Generating response...",
        )

        messages = [
            {
                "role": "system",
                "content": self.role_prompt,
            }
        ]

        if extra_context:
            messages.append(
                {
                    "role": "system",
                    "content": extra_context,
                }
            )

        messages.append(
            {
                "role": "user",
                "content": message,
            }
        )

        try:
            response = chat(
                messages,
                model=self.model,
                temperature=self.temperature,
                agent_name=self.name,
            )

            self.history.append(
                {
                    "input": message,
                    "output": response,
                }
            )

            events.emit(
                "AGENT_COMPLETED",
                agent=self.name,
                message="Completed",
            )

            return response

        except Exception as exc:
            events.emit(
                "AGENT_FAILED",
                agent=self.name,
                message=f"{type(exc).__name__}: {exc}",
            )
            raise
