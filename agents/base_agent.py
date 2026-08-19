from llm_client import chat


class Agent:
    """A single team member: a name, a role/system prompt, and a conversation memory."""

    def __init__(self, name: str, role_prompt: str, model: str | None = None, temperature: float = 0.3):
        self.name = name
        self.role_prompt = role_prompt
        self.model = model
        self.temperature = temperature
        self.history = []  # list of {"input": ..., "output": ...}

    def say(self, message: str, extra_context: str = "") -> str:
        messages = [{"role": "system", "content": self.role_prompt}]
        if extra_context:
            messages.append({"role": "system", "content": extra_context})
        messages.append({"role": "user", "content": message})

        response = chat(messages, model=self.model, temperature=self.temperature)
        self.history.append({"input": message, "output": response})
        return response
