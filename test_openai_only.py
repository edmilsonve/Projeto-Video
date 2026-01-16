import os
import sys
from services.openai_service import OpenAIService
from dotenv import load_dotenv

load_dotenv()

def test_openai_generation():
    print("--- Testing OpenAI Service ---")
    
    # Ensure key is loaded
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("[SKIPPED] OPENAI_API_KEY not found.")
        return

    service = OpenAIService(api_key=api_key)
    topic = "The Impact of Artificial Intelligence on Daily Life"
    
    script = service.generate_script(topic)
    
    if script:
        print("\n--- Generated Script Sample ---")
        print(script[:500] + "...\n(truncated)")
        print(f"Total Length: {len(script)} chars")
        print("[SUCCESS] OpenAI generated script.")
    else:
        print("[FAILED] No script returned.")

if __name__ == "__main__":
    sys.path.append(os.getcwd())
    test_openai_generation()
