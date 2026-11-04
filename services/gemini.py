"""Gemini (SDK google-genai): roteiro alternativo, transcrição com timestamps e TTS."""
import json
import os
import wave
from typing import Optional

from google import genai
from google.genai import types

from services.schemas import Transcript, VideoScript, script_prompt

# Os IDs mudam com frequência: confira em https://ai.google.dev/gemini-api/docs/models
DEFAULT_TEXT_MODEL = "gemini-flash-latest"
DEFAULT_TTS_MODEL = "gemini-3.8-flash-tts"
DEFAULT_TTS_VOICE = "Kore"
TTS_SAMPLE_RATE = 24000  # PCM 16-bit mono devolvido pelo TTS do Gemini


class GeminiService:
    def __init__(self, api_key: Optional[str] = None, client: Optional[genai.Client] = None):
        self.text_model = os.getenv("GEMINI_MODEL", DEFAULT_TEXT_MODEL)
        self.tts_model = os.getenv("GEMINI_TTS_MODEL", DEFAULT_TTS_MODEL)
        self.tts_voice = os.getenv("GEMINI_TTS_VOICE", DEFAULT_TTS_VOICE)
        self.client = client
        self.mode = "injected" if client else None
        if client is not None:
            return

        api_key = api_key or os.getenv("GEMINI_API_KEY")
        project = os.getenv("GOOGLE_CLOUD_PROJECT")
        try:
            if api_key:
                self.client = genai.Client(api_key=api_key)
                self.mode = "studio"
            elif project:
                self.client = genai.Client(
                    vertexai=True, project=project,
                    location=os.getenv("GOOGLE_CLOUD_LOCATION", "global"))
                self.mode = "vertex"
            else:
                print("Warning: set GEMINI_API_KEY or GOOGLE_CLOUD_PROJECT (Vertex AI).")
        except Exception as e:  # credenciais inválidas não devem derrubar o app
            print(f"Failed to init Gemini client: {e}")
            self.client, self.mode = None, None

    @property
    def available(self) -> bool:
        return self.client is not None

    # --- Roteiro (alternativa ao Claude) ---------------------------------------
    def generate_script(self, topic: str) -> Optional[dict]:
        if not self.client:
            print("Error: Gemini client not initialized.")
            return None
        try:
            print(f"Requesting structured script from Gemini ({self.text_model}) for: {topic}...")
            response = self.client.models.generate_content(
                model=self.text_model,
                contents=script_prompt(topic),
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=VideoScript,
                ),
            )
            script = response.parsed if isinstance(response.parsed, VideoScript) \
                else VideoScript.model_validate(json.loads(response.text))
            return script.model_dump() if script.scenes else None
        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            return None

    # --- Transcrição (substitui o Whisper/Groq) ---------------------------------
    def transcribe_audio(self, audio_path: str) -> Optional[dict]:
        """Retorna {'text', 'segments': [{'start', 'end', 'text'}]} para gerar legendas."""
        if not self.client:
            print("Error: Gemini client not initialized.")
            return None
        if not os.path.exists(audio_path):
            print(f"Error: Audio file not found at {audio_path}")
            return None
        try:
            uploaded = self.client.files.upload(file=audio_path)
            response = self.client.models.generate_content(
                model=self.text_model,
                contents=[
                    "Transcreva este áudio em português do Brasil, palavra por palavra. "
                    "Divida em trechos curtos (até ~7 palavras) com início e fim em segundos.",
                    uploaded,
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=Transcript,
                ),
            )
            transcript = response.parsed if isinstance(response.parsed, Transcript) \
                else Transcript.model_validate(json.loads(response.text))
            return transcript.model_dump()
        except Exception as e:
            print(f"Error transcribing with Gemini: {e}")
            return None

    # --- Voz (TTS) ---------------------------------------------------------------
    def synthesize_speech(self, text: str, output_path: str) -> Optional[str]:
        """Gera um .wav (PCM 24 kHz) com o TTS do Gemini."""
        if not self.client:
            print("Error: Gemini client not initialized.")
            return None
        try:
            response = self.client.models.generate_content(
                model=self.tts_model,
                contents=text,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=self.tts_voice))),
                ),
            )
            pcm = response.candidates[0].content.parts[0].inline_data.data
            with wave.open(output_path, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(TTS_SAMPLE_RATE)
                wf.writeframes(pcm)
            print(f"Gemini TTS audio saved to {output_path}")
            return output_path
        except Exception as e:
            print(f"Gemini TTS error: {e}")
            return None
