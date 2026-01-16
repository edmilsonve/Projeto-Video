import os
import sys
from core.orchestrator import VideoOrchestrator
from dotenv import load_dotenv

load_dotenv()

def test_full_pipeline():
    print("--- Testing Full Video Automation Pipeline ---")
    
    # Check keys
    required_keys = ["OPENAI_API_KEY", "GROQ_API_KEY", "STABILITY_API_KEY"]
    missing = [k for k in required_keys if not os.getenv(k)]
    if missing:
        print(f"WARNING: Missing keys: {missing}. Pipeline may fail.")
    else:
        print("All API Keys present.")

    orchestrator = VideoOrchestrator()
    
    # Use a simple topic
    topic = "The calmness of a rainy night in Tokyo"
    
    orchestrator.start_pipeline(topic)

if __name__ == "__main__":
    sys.path.append(os.getcwd())
    test_full_pipeline()
