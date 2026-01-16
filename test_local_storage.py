import os
import sys
from storage.local import LocalStorageService

def test_local_storage():
    print("--- Testing Local Storage ---")
    
    # Create dummy file
    dummy_file = "test_local_video.mp4"
    with open(dummy_file, "w") as f:
        f.write("dummy video content")
    
    storage = LocalStorageService(output_root="final_videos")
    
    saved_path = storage.save_file(dummy_file, subfolder="test_run")
    
    if saved_path and os.path.exists(saved_path):
        print(f"[SUCCESS] File verified at: {saved_path}")
    else:
        print("[FAILED] File not found at destination.")

    # Cleanup source
    if os.path.exists(dummy_file):
        os.remove(dummy_file)

if __name__ == "__main__":
    sys.path.append(os.getcwd())
    test_local_storage()
