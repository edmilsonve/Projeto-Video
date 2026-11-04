import sys
import os

# Add root to path
sys.path.append(os.getcwd())

try:
    print("--- Testing Services Import & Instantiation ---")
    
    from services.gemini import GeminiService
    from services.claude_service import ClaudeService
    from services.image_gen import ImageGenerationService, VoiceService
    from storage.drive import DriveService

    # Test Claude (chave falsa: a chamada falha e devolve None, sem derrubar o app)
    claude = ClaudeService(api_key="test_key")
    print(f"Claude: {claude.generate_script('Automation Test')}")

    # Test Gemini (roteiro alternativo + transcrição)
    gemini = GeminiService(api_key="test_key")
    print(f"Gemini: {gemini.generate_script('Automation Test')}")
    print(f"Gemini transcription: {gemini.transcribe_audio('dummy.mp3')}")

    # Test Image/Voice
    img_gen = ImageGenerationService(stability_key="test_key")
    img_gen.generate_image("A futuristic city", "output_image.png")
    
    voice = VoiceService()
    voice.generate_voice("Hello World", "output_audio.wav")

    # Test Drive
    # Creating a dummy file to upload
    with open("test_upload.txt", "w") as f:
        f.write("test content")
    
    drive = DriveService(folder_id="12345")
    drive.upload_file("test_upload.txt")
    
    # Clean up
    if os.path.exists("test_upload.txt"):
        os.remove("test_upload.txt")

    print("[SUCCESS] All service stubs initialized and methods called.")

except Exception as e:
    print(f"[ERROR] Service verification failed: {e}")
    sys.exit(1)
