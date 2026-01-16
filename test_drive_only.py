import os
import sys
from storage.drive import DriveService
from dotenv import load_dotenv

load_dotenv()

def test_drive_upload():
    print("--- Testing Drive Upload ---")
    
    # Check if credentials exist
    creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not creds or not os.path.exists(creds):
        print(f"[SKIPPED] Credentials file not found at: {creds}")
        return

    # Create dummy file
    dummy_file = "test_drive_upload.txt"
    with open(dummy_file, "w") as f:
        f.write("This is a test upload from Python Automation.")

    service = DriveService()
    
    # We might not have a folder ID, so it will upload to root (My Drive of Service Account)
    if not service.folder_id:
         print("Note: No Folder ID set. Uploading to Service Account's Root Drive.")
    
    file_id = service.upload_file(dummy_file)
    
    if file_id:
        print(f"[SUCCESS] File uploaded successfully. ID: {file_id}")
    else:
        print("[FAILED] Upload failed.")

    # Cleanup
    if os.path.exists(dummy_file):
        os.remove(dummy_file)

if __name__ == "__main__":
    sys.path.append(os.getcwd())
    test_drive_upload()
