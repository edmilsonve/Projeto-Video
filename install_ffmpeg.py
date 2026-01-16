import os
import zipfile
import shutil
import urllib.request
import sys

FFMPEG_URL = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
INSTALL_DIR = "ffmpeg_bin"

def download_and_install_ffmpeg():
    print(f"--- Installing FFMPEG Locally to {INSTALL_DIR} ---")
    
    if os.path.exists(INSTALL_DIR):
        print(f"Directory {INSTALL_DIR} already exists. checking content...")
        if os.path.exists(os.path.join(INSTALL_DIR, "bin", "ffmpeg.exe")):
            print("FFMPEG already installed.")
            return

    # Download
    zip_path = "ffmpeg.zip"
    print(f"Downloading FFMPEG from {FFMPEG_URL}...")
    try:
        urllib.request.urlretrieve(FFMPEG_URL, zip_path)
        print("Download complete.")
    except Exception as e:
        print(f"Failed to download FFMPEG: {e}")
        return

    # Extract
    print("Extracting...")
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall("ffmpeg_temp")
            
        # Move bin folder
        # The zip usually contains a root folder like 'ffmpeg-master-latest-win64-gpl'
        extracted_root = os.listdir("ffmpeg_temp")[0]
        full_extracted_path = os.path.join("ffmpeg_temp", extracted_root)
        
        # We want the 'bin' folder from there
        if os.path.exists(INSTALL_DIR):
             shutil.rmtree(INSTALL_DIR)
        
        shutil.move(full_extracted_path, INSTALL_DIR)
        print(f"FFMPEG installed to {os.path.abspath(INSTALL_DIR)}")
        
    except Exception as e:
        print(f"Failed to extract: {e}")
    finally:
        # Cleanup
        if os.path.exists(zip_path):
            os.remove(zip_path)
        if os.path.exists("ffmpeg_temp"):
            shutil.rmtree("ffmpeg_temp")

if __name__ == "__main__":
    download_and_install_ffmpeg()
