import os
from openai import OpenAI

class OpenAIService:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            print("Warning: OPENAI_API_KEY not found in environment.")
            self.client = None
        else:
            self.client = OpenAI(api_key=self.api_key)

    def generate_script(self, topic: str) -> dict:
        """
        Generates a structured video script (JSON) for the given topic.
        Returns a dict with a list of scenes.
        """
        if not self.client:
            print("Error: OpenAI Client not initialized.")
            return None

        prompt = (
            f"Create a video script for YouTube Shorts about: '{topic}'.\n"
            "Constraints:\n"
            "1. Output MUST be valid JSON with this structure: {'scenes': [{'text': '...', 'visual': '...'}]}\n"
            "2. Language: Portuguese (Brazil).\n"
            "3. Divide story into 3-5 scenes.\n"
            "4. Each scene MUST be max 30 seconds (approx 60 words).\n"
            "5. 'visual': A detailed English prompt for an AI image generator (Stable Diffusion). Style: Cinematic, Photorealistic, 8k, Unreal Engine 5 render, dramatic lighting.\n"
            "6. 'text': The narration text in Portuguese.\n"
            "7. No markdown formatting (like ```json), just raw JSON string."
        )

        try:
            print(f"Requesting structure script (JSON) from OpenAI for: {topic}...")
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a scriptwriter assistance. You output only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content
            import json
            script_json = json.loads(content)
            
            print(f"Generated {len(script_json.get('scenes', []))} scenes.")
            return script_json
            
        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            return None
            
        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            return None
