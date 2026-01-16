import os
import sys
from services.image_gen import ImageGenerationService, VoiceService
from dotenv import load_dotenv

load_dotenv()

def test_media_services():
    print("--- Testing Media Services ---")
    
    # 1. Voice Test (OpenAI TTS as fallback/primary)
    print("\n[Voice Test]")
    voice_service = VoiceService()
    voice_out = "test_voice.mp3"
    result_audio = voice_service.generate_voice("Hello, this is a test of the automatic video system.", voice_out)
    
    if result_audio and os.path.exists(result_audio):
        print(f"[SUCCESS] Voice generated at: {result_audio}")
        # cleanup
        # os.remove(result_audio)
    else:
        print("[FAILED] Voice generation failed or no key available.")

    # 2. Image Test
    print("\n[Image Test]")
    img_service = ImageGenerationService()
    img_out = "test_image.png"
    
    if not img_service.stability_key and not img_service.replicate_token:
        print("[SKIPPED] No Stability/Replicate keys found.")
    else:
        result_img = img_service.generate_image("A futuristic robot painting a canvas, cyberpunk style", img_out)
        if result_img and os.path.exists(result_img):
            print(f"[SUCCESS] Image generated at: {result_img}")
            # cleanup
            # os.remove(result_img)
        else:
            print("[FAILED] Image generation failed.")

if __name__ == "__main__":
    sys.path.append(os.getcwd())
    test_media_services()
