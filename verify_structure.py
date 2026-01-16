import sys
import os

# Add the current directory to the python path to allow imports
sys.path.append(os.getcwd())

try:
    from core.orchestrator import VideoOrchestrator
    from utils.text import slugify
    from utils.video import get_ffmpeg_template, get_karaoke_ass_header

    print("--- Testing Slugify ---")
    slug = slugify("Test Video: Automação Python & n8n!")
    print(f"Original: 'Test Video: Automação Python & n8n!' -> Slug: '{slug}'")
    assert slug == "test-video-automacao-python-n8n"

    print("\n--- Testing VideoOrchestrator ---")
    orch = VideoOrchestrator(topic="Video Automation Project")
    print(f"Orchestrator initialized for topic: {orch.topic}")
    print(f"Slug: {orch.slug}")
    print(f"State Status: {orch.state['status']}")
    print(f"Temp Dir: {orch.temp_dir}")
    
    orch.update_step("script", {"content": "Hello World"})
    print("Step 'script' updated.")

    print("\n--- Testing FFMPEG Template ---")
    template = get_ffmpeg_template()
    print(f"Template starts with: {template[:20]}...")
    
    print("\n--- Testing Karaoke Header ---")
    header = get_karaoke_ass_header("My Song")
    print(f"Header contains Title: {'Title: My Song' in header}")

    print("\n[SUCCESS] All checks passed.")

except ImportError as e:
    print(f"[ERROR] Import failed: {e}")
    sys.exit(1)
except AssertionError as e:
    print(f"[ERROR] Assertion failed: {e}")
    sys.exit(1)
except Exception as e:
    print(f"[ERROR] Unexpected error: {e}")
    sys.exit(1)
