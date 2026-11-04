"""Contratos compartilhados entre os provedores de roteiro (Claude e Gemini)."""
from typing import List

from pydantic import BaseModel, Field


class Scene(BaseModel):
    text: str = Field(description="Narração da cena em português do Brasil (até ~60 palavras).")
    visual: str = Field(description="Prompt detalhado, em inglês, para o gerador de imagem.")


class VideoScript(BaseModel):
    title: str = Field(description="Título do vídeo, até 60 caracteres, palavra-chave no início.")
    hook: str = Field(description="Gancho dos primeiros 20 segundos.")
    scenes: List[Scene]


class TranscriptSegment(BaseModel):
    start: float = Field(description="Início do trecho em segundos.")
    end: float = Field(description="Fim do trecho em segundos.")
    text: str


class Transcript(BaseModel):
    text: str
    segments: List[TranscriptSegment]


def script_prompt(topic: str) -> str:
    """Prompt único usado pelos dois provedores, para que a saída seja equivalente."""
    return (
        f"Crie o roteiro de um YouTube Short sobre: '{topic}'.\n"
        "Regras:\n"
        "1. Idioma da narração: português do Brasil, tom natural, sem clichês de IA.\n"
        "2. De 3 a 5 cenas, cada uma com no máximo ~60 palavras (até 30 s).\n"
        "3. A primeira cena é o gancho e já entrega parte da promessa do título.\n"
        "4. 'visual' em inglês, para Stable Diffusion: cinematic, photorealistic, "
        "dramatic lighting; sem marcas registradas nem rostos de pessoas reais.\n"
        "5. Não invente dados; se não tiver certeza, formule sem números."
    )
