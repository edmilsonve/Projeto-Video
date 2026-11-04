"""Testes sem rede: os clientes do Claude e do Gemini são substituídos por dublês."""
import os
import wave
from types import SimpleNamespace

import pytest

from services.claude_service import ClaudeService
from services.gemini import GeminiService
from services.image_gen import VoiceService
from services.schemas import Scene, Transcript, TranscriptSegment, VideoScript
from services.script_router import ScriptRouter

SCRIPT = VideoScript(title="Café no Brasil", hook="Você bebe história todo dia.",
                     scenes=[Scene(text="Cena 1", visual="coffee farm, cinematic")])


class FakeMessages:
    def __init__(self, stop_reason="end_turn", parsed=SCRIPT):
        self.stop_reason, self.parsed, self.calls = stop_reason, parsed, []

    def parse(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(
            stop_reason=self.stop_reason, parsed_output=self.parsed, _request_id="req_test",
            usage=SimpleNamespace(input_tokens=10, output_tokens=20, cache_read_input_tokens=0))


def claude_with(messages):
    return ClaudeService(client=SimpleNamespace(messages=messages), model="test-model", effort="low")


def test_claude_returns_structured_script_and_uses_cache():
    messages = FakeMessages()
    result = claude_with(messages).generate_script("café")
    assert result["title"] == "Café no Brasil"
    assert result["scenes"][0]["visual"] == "coffee farm, cinematic"
    call = messages.calls[0]
    assert call["output_format"] is VideoScript
    assert call["output_config"] == {"effort": "low"}
    assert call["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert call["model"] == "test-model"


@pytest.mark.parametrize("stop_reason", ["refusal", "max_tokens"])
def test_claude_incomplete_responses_return_none(stop_reason):
    assert claude_with(FakeMessages(stop_reason=stop_reason)).generate_script("x") is None


def test_claude_without_key_is_unavailable(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
    service = ClaudeService()
    assert not service.available
    assert service.generate_script("x") is None


class Provider:
    def __init__(self, result, available=True):
        self.result, self.available, self.called = result, available, False

    def generate_script(self, topic):
        self.called = True
        return self.result


def test_router_falls_back_to_gemini_when_claude_fails():
    claude, gemini = Provider(None), Provider(SCRIPT.model_dump())
    assert ScriptRouter(claude, gemini).generate_script("x")["title"] == "Café no Brasil"
    assert claude.called and gemini.called


def test_router_skips_unavailable_provider():
    claude, gemini = Provider(SCRIPT.model_dump(), available=False), Provider(SCRIPT.model_dump())
    ScriptRouter(claude, gemini).generate_script("x")
    assert not claude.called and gemini.called


class FakeModels:
    def __init__(self, parsed=None, audio=b""):
        self.parsed, self.audio, self.calls = parsed, audio, []

    def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        part = SimpleNamespace(inline_data=SimpleNamespace(data=self.audio))
        return SimpleNamespace(
            parsed=self.parsed, text="",
            candidates=[SimpleNamespace(content=SimpleNamespace(parts=[part]))])


def gemini_with(models):
    files = SimpleNamespace(upload=lambda file: f"uploaded:{file}")
    return GeminiService(client=SimpleNamespace(models=models, files=files))


def test_gemini_script_uses_json_schema():
    models = FakeModels(parsed=SCRIPT)
    assert gemini_with(models).generate_script("café")["hook"].startswith("Você")
    config = models.calls[0]["config"]
    assert config.response_mime_type == "application/json"
    assert config.response_schema is VideoScript


def test_gemini_transcription_returns_segments(tmp_path):
    audio = tmp_path / "a.wav"
    audio.write_bytes(b"RIFF")
    transcript = Transcript(text="olá mundo", segments=[TranscriptSegment(start=0, end=1.2, text="olá mundo")])
    result = gemini_with(FakeModels(parsed=transcript)).transcribe_audio(str(audio))
    assert result["segments"][0]["end"] == 1.2


def test_gemini_tts_writes_wav(tmp_path):
    out = tmp_path / "voz.wav"
    pcm = b"\x00\x00" * 2400  # 0,1 s de silêncio a 24 kHz
    assert gemini_with(FakeModels(audio=pcm)).synthesize_speech("olá", str(out)) == str(out)
    with wave.open(str(out)) as wf:
        assert (wf.getframerate(), wf.getnchannels(), wf.getnframes()) == (24000, 1, 2400)


def test_voice_service_falls_back_to_gemini(monkeypatch, tmp_path):
    monkeypatch.setenv("VOICE_PROVIDER", "auto")
    gemini = gemini_with(FakeModels(audio=b"\x00\x00" * 10))
    voice = VoiceService(gemini_service=gemini)
    monkeypatch.setattr(voice, "_kokoro", lambda text, path: None)  # Kokoro não instalado
    out = tmp_path / "v.wav"
    assert voice.generate_voice("olá", str(out)) == str(out)
    assert os.path.exists(out)


def test_orchestrator_has_no_openai_or_groq(monkeypatch, tmp_path):
    for key in ("ANTHROPIC_API_KEY", "GEMINI_API_KEY", "GOOGLE_CLOUD_PROJECT"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.chdir(tmp_path)
    from core.orchestrator import VideoOrchestrator
    orch = VideoOrchestrator()
    names = {type(p).__name__ for p in orch.script_service.providers}
    assert names == {"ClaudeService", "GeminiService"}
