import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

class DriveService:
    SCOPES = ['https://www.googleapis.com/auth/drive.file']

    def __init__(self, folder_id=None):
        self.folder_id = folder_id or os.getenv("GOOGLE_DRIVE_FOLDER_ID")
        self.creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        self.service = None

        if self.creds_path and os.path.exists(self.creds_path):
            try:
                creds = service_account.Credentials.from_service_account_file(
                    self.creds_path, scopes=self.SCOPES)
                self.service = build('drive', 'v3', credentials=creds)
                print("Google Drive Service initialized.")
            except Exception as e:
                print(f"Failed to init Drive Service: {e}")
        else:
            print("Warning: GOOGLE_APPLICATION_CREDENTIALS not found/invalid.")

    def upload_file(self, file_path: str, destination_name: str = None) -> str:
        """
        Uploads a file to Google Drive.
        Returns the File ID or None on failure.
        """
        if not self.service:
            print("Error: Drive Service not initialized.")
            return None

        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return None
        
        name = destination_name or os.path.basename(file_path)
        
        file_metadata = {'name': name}
        if self.folder_id:
            file_metadata['parents'] = [self.folder_id]

        media = MediaFileUpload(file_path, resumable=True)

        try:
            print(f"Uploading {name} to Drive...")
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            file_id = file.get('id')
            print(f"Upload Complete. File ID: {file_id}")
            return file_id
            
        except Exception as e:
            print(f"Upload failed: {e}")
            return None
