"""Escolhe o provedor de roteiro: Claude primeiro, Gemini como alternativa."""
from typing import Optional


class ScriptRouter:
    def __init__(self, primary, fallback=None):
        self.providers = [p for p in (primary, fallback) if p is not None]

    def generate_script(self, topic: str) -> Optional[dict]:
        for provider in self.providers:
            if not getattr(provider, "available", True):
                continue
            script = provider.generate_script(topic)
            if script and script.get("scenes"):
                return script
            print(f"{type(provider).__name__} failed; trying next provider...")
        print("No script provider succeeded.")
        return None
