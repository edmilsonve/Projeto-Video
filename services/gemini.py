import os
import vertexai
from vertexai.preview.generative_models import GenerativeModel
import google.auth

class GeminiService:
    def __init__(self, project_id=None, location="us-central1"):
        # Prioritize API Key (Google AI Studio - Free Tier available)
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        
        if self.api_key:
            print("Initializing Gemini via Google AI Studio (API Key).")
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash')
            self.mode = "studio"
        
        elif self.creds_path and os.path.exists(self.creds_path):
            print(f"Initializing Vertex AI with credentials: {self.creds_path}")
            try:
                creds, project = google.auth.default()
                self.project_id = project_id or project
                vertexai.init(project=self.project_id, location=location)
                self.model = GenerativeModel("gemini-2.0-flash")
                self.mode = "vertex"
            except Exception as e:
                print(f"Failed to init Vertex AI: {e}")
                self.mode = "error"
        
        else:
            print("Warning: No valid credentials found (Set GEMINI_API_KEY or GOOGLE_APPLICATION_CREDENTIALS).")
            self.mode = None

    def generate_script(self, topic: str) -> str:
        """
        Generates a video script for the given topic.
        """
        if not self.mode:
             print("Error: Gemini Service not initialized.")
             return None

        prompt = (
            f"Create a compelling video script for YouTube Shorts about: '{topic}'.\n"
            "Constraints:\n"
            "1. The length MUST be between 2300 and 2400 characters.\n"
            "2. Tone: Engaging, informative, and viral.\n"
            "3. Structure: Hook, Body, Conclusion.\n"
            "4. Output ONLY the raw text of the script, no meta-comments."
        )

        try:
            print(f"Requesting script from Gemini ({self.mode}) for topic: {topic}...")
            response = self.model.generate_content(prompt)
            
            # Vertex AI and Studio have slightly different response objects but .text usually works for both
            script_text = response.text
            
            char_count = len(script_text)
            print(f"Generated script length: {char_count} characters.")
            
            return script_text
            
        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            # If rate limit, maybe print specific advice
            if "429" in str(e):
                print("Hit Rate Limit (429). Waiting/Retrying might help.")
            return None
