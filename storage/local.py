import os
import shutil
import time

class LocalStorageService:
    def __init__(self, output_root="output"):
        self.output_root = output_root
        if not os.path.exists(self.output_root):
            os.makedirs(self.output_root)
            print(f"Created output directory: {self.output_root}")

    def save_file(self, file_path: str, subfolder: str = None) -> str:
        """
        Saves a file to the local output directory.
        Returns the absolute path of the saved file.
        """
        if not os.path.exists(file_path):
            print(f"Error: File not found {file_path}")
            return None

        # Determine destination
        dest_dir = self.output_root
        if subfolder:
            dest_dir = os.path.join(self.output_root, subfolder)
            os.makedirs(dest_dir, exist_ok=True)

        filename = os.path.basename(file_path)
        # Add timestamp to avoid overwriting or just keep original name? 
        # Requirement said to "Move", but copying is safer during debug.
        
        dest_path = os.path.join(dest_dir, filename)
        
        try:
            shutil.copy2(file_path, dest_path)
            print(f"File saved locally at: {dest_path}")
            return dest_path
        except Exception as e:
            print(f"Error saving file locally: {e}")
            return None
