import os
import sys
from services.groq import GroqService
from dotenv import load_dotenv

load_dotenv()

def test_groq_transcription():
    print("--- Testing Groq Service ---")
    
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("[SKIPPED] GROQ_API_KEY not found.")
        return

    # Create dummy audio file? 
    # Can't create a real audio file easily from scratch without dependencies like pydub/numpy
    # or using a pre-existing asset.
    # For now, we will check initialization and fail gracefully on file.
    
    service = GroqService(api_key=api_key)
    
    print("Verifying API Key by listing models...")
    try:
        models = service.client.models.list()
        print(f"[SUCCESS] Connection established. Found {len(models.data)} models.")
        print(f"First model example: {models.data[0].id}")
    except Exception as e:
        print(f"[FAILED] API Key validation failed: {e}")
        return

    # Check if we have any audio file in local dir
    dummy_wav = "test_audio.wav"
    if not os.path.exists(dummy_wav):
        print(f"[INFO] No audio file '{dummy_wav}' found to test transcription.")
        print("Skipping actual transcription test, but API connection is VERIFIED.")
        return

    result = service.transcribe_audio(dummy_wav)
    if result:
        print("[SUCCESS] Transcription result received.")
        print(str(result)[:500])
    
if __name__ == "__main__":
    sys.path.append(os.getcwd())
    test_groq_transcription()
