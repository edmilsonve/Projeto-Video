"""Google Drive: envio dos vídeos renderizados e download no job de publicação.

Autenticação por Application Default Credentials (google.auth.default):
- no GitHub Actions: Workload Identity Federation (OIDC), sem nenhuma chave guardada;
- localmente: `gcloud auth application-default login` ou GOOGLE_APPLICATION_CREDENTIALS.
Atenção: contas de serviço não têm cota própria no Drive. Para ENVIAR, prefira o
Google Drive para computador (pasta sincronizada) ou um drive compartilhado.
"""
import io
import os

SCOPE_FILE = "https://www.googleapis.com/auth/drive.file"
SCOPE_READONLY = "https://www.googleapis.com/auth/drive.readonly"


class DriveService:
    def __init__(self, folder_id=None, readonly=False, service=None):
        self.folder_id = folder_id or os.getenv("GOOGLE_DRIVE_FOLDER_ID")
        self.service = service
        if service is not None:
            return
        try:
            import google.auth
            from googleapiclient.discovery import build

            creds, _ = google.auth.default(scopes=[SCOPE_READONLY if readonly else SCOPE_FILE])
            self.service = build("drive", "v3", credentials=creds, cache_discovery=False)
            print("Google Drive Service initialized.")
        except Exception as e:  # sem credenciais: o app continua, só sem Drive
            print(f"Warning: Drive indisponível ({type(e).__name__}).")

    def upload_file(self, file_path: str, destination_name: str = None) -> str:
        """Envia um arquivo e devolve o ID (ou None em caso de falha)."""
        if not self.service:
            print("Error: Drive Service not initialized.")
            return None
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return None
        from googleapiclient.http import MediaFileUpload

        name = destination_name or os.path.basename(file_path)
        metadata = {"name": name, **({"parents": [self.folder_id]} if self.folder_id else {})}
        try:
            file = self.service.files().create(
                body=metadata, media_body=MediaFileUpload(file_path, resumable=True),
                fields="id", supportsAllDrives=True).execute()
            return file.get("id")
        except Exception as e:
            print(f"Upload failed: {e}")
            return None

    def find_file(self, name: str):
        """Procura um arquivo pelo nome exato dentro da pasta configurada."""
        if not self.service or not self.folder_id:
            return None
        safe = name.replace("\\", "\\\\").replace("'", "\\'")
        query = f"name = '{safe}' and '{self.folder_id}' in parents and trashed = false"
        result = self.service.files().list(q=query, fields="files(id, name, size)", pageSize=2,
                                           supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
        files = result.get("files", [])
        if len(files) > 1:
            raise RuntimeError(f"mais de um arquivo chamado {name!r} na pasta do Drive")
        return files[0] if files else None

    def download_file(self, file_id: str, dest_path: str) -> str:
        from googleapiclient.http import MediaIoBaseDownload

        request = self.service.files().get_media(fileId=file_id, supportsAllDrives=True)
        with io.FileIO(dest_path, "wb") as fh:
            downloader = MediaIoBaseDownload(fh, request, chunksize=16 * 1024 * 1024)
            done = False
            while not done:
                _, done = downloader.next_chunk()
        return dest_path
