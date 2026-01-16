import os
from groq import Groq

class GroqService:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            print("Warning: GROQ_API_KEY not found in environment.")
            self.client = None
        else:
            self.client = Groq(api_key=self.api_key)

    def transcribe_audio(self, audio_path: str) -> str:
        """
        Transcribes the audio file using Groq (Whisper).
        Returns the transcription object or text.
        For automation, we usually need word-level timestamps for Karaoke.
        """
        if not self.client:
            print("Error: Groq Client not initialized.")
            return None
            
        if not os.path.exists(audio_path):
            print(f"Error: Audio file not found at {audio_path}")
            return None

        try:
            print(f"Transcribing {audio_path} using Groq Whisper...")
            with open(audio_path, "rb") as file:
                # https://console.groq.com/docs/speech-text
                transcription = self.client.audio.transcriptions.create(
                    file=(os.path.basename(audio_path), file.read()),
                    model="whisper-large-v3",
                    response_format="verbose_json", # Needed for timestamps
                )
            
            # For now, returning the raw text or the object. 
            # In a real scenario, we would parse 'segments' for .ass creation.
            print("Transcription complete.")
            return transcription
            
        except Exception as e:
            print(f"Error calling Groq API: {e}")
            return None
