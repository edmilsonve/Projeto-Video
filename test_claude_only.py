import os
import sys
from dotenv import load_dotenv

load_dotenv()


def test_claude_generation():
    print("--- Testing Claude Service Isolation ---")
    from services.claude_service import ClaudeService

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("[SKIPPED] ANTHROPIC_API_KEY not found.")
        return
    script = ClaudeService().generate_script("A história do café no Brasil")
    if script:
        print(f"Title: {script['title']} | Scenes: {len(script['scenes'])}")
        print("[SUCCESS] Claude generated script.")
    else:
        print("[FAILED] No script returned.")


if __name__ == "__main__":
    sys.path.append(os.getcwd())
    test_claude_generation()
