import os
import sys
from services.gemini import GeminiService
from dotenv import load_dotenv

# Load env vars
load_dotenv()

def test_gemini_generation():
    print("--- Testing Gemini Service Isolation ---")
    
    # The Service now handles auth internally (Vertex or Studio)
    service = GeminiService()
    
    if not service.mode:
        print("[FAILED] Gemini Service could not initialize (no Key or Service Account).")
        return

    print(f"Gemini initialized in mode: {service.mode}")
    
    topic = "The Future of AI Agents"
    
    script = service.generate_script(topic)
    
    if script:
        print("\n--- Generated Script Sample ---")
        print(script[:500] + "...\n(truncated)")
        print(f"Total Length: {len(script)} chars")
        print("[SUCCESS] Gemini generated script.")
    else:
        print("[FAILED] No script returned.")

if __name__ == "__main__":
    # Add root to path
    sys.path.append(os.getcwd())
    test_gemini_generation()
