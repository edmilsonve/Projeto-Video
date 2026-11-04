"""Geração de roteiro com Claude (SDK oficial da Anthropic), com saída estruturada."""
import os
from typing import Optional

import anthropic

from services.schemas import VideoScript, script_prompt

# Tier de custo/qualidade configurável por variável de ambiente (ver .env.example).
DEFAULT_SCRIPT_MODEL = "claude-sonnet-5-5"
DEFAULT_EFFORT = "medium"

SYSTEM_PROMPT = (
    "Você é roteirista de canais do YouTube sem rosto. Escreve roteiros originais, "
    "com ângulo próprio, ritmo variado e fatos verificáveis. Nunca copia vídeos "
    "existentes e nunca promete o que o vídeo não entrega."
)


class ClaudeService:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None,
                 effort: Optional[str] = None, client: Optional[anthropic.Anthropic] = None):
        self.model = model or os.getenv("CLAUDE_MODEL_SCRIPT", DEFAULT_SCRIPT_MODEL)
        self.effort = effort or os.getenv("CLAUDE_EFFORT_SCRIPT", DEFAULT_EFFORT)
        if client is not None:
            self.client = client
        elif api_key or os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_AUTH_TOKEN"):
            self.client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()
        else:
            print("Warning: ANTHROPIC_API_KEY not found in environment.")
            self.client = None

    @property
    def available(self) -> bool:
        return self.client is not None

    def generate_script(self, topic: str) -> Optional[dict]:
        """Retorna {'title', 'hook', 'scenes': [{'text', 'visual'}]} ou None em caso de falha."""
        if not self.client:
            print("Error: Claude client not initialized.")
            return None
        try:
            print(f"Requesting structured script from Claude ({self.model}) for: {topic}...")
            response = self.client.messages.parse(
                model=self.model,
                max_tokens=16000,
                # Prefixo estável e cacheado: só o tema muda entre chamadas.
                system=[{"type": "text", "text": SYSTEM_PROMPT,
                         "cache_control": {"type": "ephemeral"}}],
                messages=[{"role": "user", "content": script_prompt(topic)}],
                output_config={"effort": self.effort},
                output_format=VideoScript,
            )
            if response.stop_reason == "refusal":
                print("Claude declined the request (refusal).")
                return None
            if response.stop_reason == "max_tokens":
                print("Claude hit max_tokens before finishing the script.")
                return None
            script = response.parsed_output
            if script is None or not script.scenes:
                print("Claude returned no scenes.")
                return None
            usage = response.usage
            print(f"Claude usage: in={usage.input_tokens} out={usage.output_tokens} "
                  f"cache_read={getattr(usage, 'cache_read_input_tokens', 0)} "
                  f"request_id={response._request_id}")
            return script.model_dump()
        except anthropic.RateLimitError:
            print("Claude rate limited (429) after SDK retries.")
        except anthropic.APIStatusError as e:
            print(f"Claude API error {e.status_code}: {e.message}")
        except anthropic.APIConnectionError:
            print("Claude connection error.")
        return None
