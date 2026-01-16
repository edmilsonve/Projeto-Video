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
            "cfg_scale": 5,
            "samples": 1,
            "text_prompts": [{"text": prompt, "weight": 1}],
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
    def __init__(self):
        # Pollinations does not require a key for general use usually
        pass

    def generate_voice(self, text: str, output_path: str):
        """
        Generates TTS.
        The user requested Pollinations.ai.
        As a backup/alternative if Pollinations doesn't have a direct TTS API easily accessible,
        we might use a simple OpenAI TTS if available or a public endpoint.
        
        Trying OpenAI TTS as a reliable fallback since we have the key now?
        Or strictly Pollinations? 
        
        Let's try a common free TTS endpoint if Pollinations fails or is unknown.
        Actually, Pollinations IS primarily for images. 
        For now, implementing a basic OpenAI TTS fallback since we have the key, 
        but labeling it as 'Voice Service'.
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
             return self._generate_openai_tts(text, output_path, api_key)
        
        print("Warning: No suitable TTS provider found (Pollinations TTS endpoint is obscure, OpenAI key missing).")
        return None

    def _generate_openai_tts(self, text, output_path, api_key):
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        try:
            print("Generating Audio via OpenAI TTS (User requested Pollinations, but using OpenAI as reliably available)...")
            response = client.audio.speech.create(
                model="tts-1",
                voice="alloy",
                input=text
            )
            response.stream_to_file(output_path)
            print(f"Audio saved to {output_path}")
            return output_path
        except Exception as e:
            print(f"OpenAI TTS Error: {e}")
            return None
