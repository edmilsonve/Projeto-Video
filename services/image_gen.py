import os
import requests

class ImageGenerationService:
    def __init__(self, stability_key=None, replicate_token=None):
        self.stability_key = stability_key or os.getenv("STABILITY_API_KEY")
        self.replicate_token = replicate_token or os.getenv("REPLICATE_API_TOKEN")

    def generate_image(self, prompt: str, output_path: str):
        """
        Generates an image based on the prompt.
        Prioritizes Stability AI, falls back to Replicate.
        """
        print(f"Generating image for prompt: '{prompt}'")
        
        if self.stability_key:
            return self._generate_stability(prompt, output_path)
        elif self.replicate_token:
            print("Stability Key not found. Trying Replicate...")
            return self._generate_replicate(prompt, output_path)
        else:
            print("Error: No Image Gen keys found (Stability/Replicate).")
            return None

    def _generate_stability(self, prompt, output_path):
        # https://platform.stability.ai/docs/api-reference#tag/v1generation/operation/textToImage
        url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.stability_key}"
        }
        body = {
            "steps": 40,
            "width": 1024,
            "height": 1024,
            "seed": 0,
            "cfg_scale": 7,
            "samples": 1,
            "text_prompts": [{"text": prompt, "weight": 1}],
            "style_preset": "cinematic"
        }
        
        try:
            response = requests.post(url, headers=headers, json=body)
            if response.status_code != 200:
                print(f"Stability Error: {response.text}")
                return None
            
            data = response.json()
            # Decode base64
            import base64
            for i, image in enumerate(data["artifacts"]):
                with open(output_path, "wb") as f:
                    f.write(base64.b64decode(image["base64"]))
                print(f"Stability Image saved to {output_path}")
                return output_path
                
        except Exception as e:
            print(f"Stability Exception: {e}")
            return None

    def _generate_replicate(self, prompt, output_path):
        # Placeholder for Replicate logic (requires 'replicate' lib usually)
        print("Replicate logic not yet implemented (Need 'replicate' lib).")
        return None


class VoiceService:
    """TTS sem OpenAI: Kokoro local (grátis, Apache 2.0) e, como alternativa, TTS do Gemini.

    VOICE_PROVIDER = auto (padrão) | kokoro | gemini
    """

    def __init__(self, gemini_service=None):
        self.provider = os.getenv("VOICE_PROVIDER", "auto").lower()
        self.kokoro_lang = os.getenv("KOKORO_LANG", "p")        # 'p' = português do Brasil
        self.kokoro_voice = os.getenv("KOKORO_VOICE", "pf_dora")
        self._gemini = gemini_service
        self._kokoro_pipeline = None

    def generate_voice(self, text: str, output_path: str):
        """Gera um .wav e devolve o caminho, ou None se nenhum provedor funcionar."""
        order = {"kokoro": ["kokoro"], "gemini": ["gemini"]}.get(self.provider, ["kokoro", "gemini"])
        for name in order:
            path = self._kokoro(text, output_path) if name == "kokoro" else self._gemini_tts(text, output_path)
            if path:
                return path
        print("Warning: no TTS provider available (install kokoro or set GEMINI_API_KEY).")
        return None

    def _kokoro(self, text, output_path):
        try:
            from kokoro import KPipeline
            import numpy as np
            import soundfile as sf
        except ImportError:
            return None  # Kokoro é opcional: pip install -r requirements-local-tts.txt
        try:
            if self._kokoro_pipeline is None:
                self._kokoro_pipeline = KPipeline(lang_code=self.kokoro_lang)
            chunks = [audio for _, _, audio in self._kokoro_pipeline(text, voice=self.kokoro_voice)]
            if not chunks:
                return None
            sf.write(output_path, np.concatenate(chunks), 24000)
            print(f"Kokoro audio saved to {output_path}")
            return output_path
        except Exception as e:
            print(f"Kokoro TTS error: {e}")
            return None

    def _gemini_tts(self, text, output_path):
        if self._gemini is None:
            from services.gemini import GeminiService
            self._gemini = GeminiService()
        if not self._gemini.available:
            return None
        return self._gemini.synthesize_speech(text, output_path)
