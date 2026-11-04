"""Publicação no YouTube pela Data API v3 oficial (OAuth do dono do canal).

Segurança:
- Escopo mínimo: youtube.upload (envio do vídeo e da thumbnail). Nada de youtube completo.
- O refresh token NUNCA fica no repositório. Ordem de busca: variáveis de ambiente
  (secrets do ambiente protegido no GitHub Actions) → ~/.config/darkstudio/youtube.json
  (arquivo 0600 fora do repositório, criado por scripts/youtube_auth.py).
- O vídeo sobe sempre como PRIVADO com publishAt: quem torna público, na hora marcada,
  é o próprio YouTube. A publicação nunca depende de uma máquina ligada.
"""
import json
import os
import random
import stat
import time
from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
TOKEN_URI = "https://oauth2.googleapis.com/token"
LOCAL_CREDENTIALS = os.path.expanduser("~/.config/darkstudio/youtube.json")
RETRIABLE_STATUS = {500, 502, 503, 504}
MAX_RETRIES = 6


class PublishMetadata(BaseModel):
    title: str = Field(max_length=100)
    description: str = Field(default="", max_length=5000)
    tags: List[str] = Field(default_factory=list)
    category_id: str = "27"                    # Educação; ajuste por canal
    default_language: str = "pt-BR"
    publish_at: str                            # ISO 8601 com fuso, ex.: 2026-11-10T18:00:00-03:00
    contains_synthetic_media: bool             # obrigatório: voz/imagem realista de IA → True
    made_for_kids: bool = False
    video_file: str                            # nome do arquivo (local em final_videos/ ou no Drive)
    thumbnail_file: Optional[str] = None
    playlist_id: Optional[str] = None          # exige escopo maior; adicione manualmente se precisar

    @field_validator("title")
    @classmethod
    def no_angle_brackets(cls, v):
        if "<" in v or ">" in v:
            raise ValueError("o YouTube recusa '<' e '>' no título")
        return v

    @field_validator("tags")
    @classmethod
    def tags_limit(cls, v):
        if sum(len(t) + 2 for t in v) > 500:
            raise ValueError("tags somam mais de 500 caracteres")
        return v

    @field_validator("publish_at")
    @classmethod
    def future_with_timezone(cls, v):
        when = datetime.fromisoformat(v.replace("Z", "+00:00"))
        if when.tzinfo is None:
            raise ValueError("publish_at precisa de fuso horário (ex.: -03:00)")
        if when <= datetime.now(timezone.utc):
            raise ValueError("publish_at precisa estar no futuro")
        return when.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_body(meta: PublishMetadata) -> dict:
    return {
        "snippet": {
            "title": meta.title,
            "description": meta.description,
            "tags": meta.tags,
            "categoryId": meta.category_id,
            "defaultLanguage": meta.default_language,
            "defaultAudioLanguage": meta.default_language,
        },
        "status": {
            "privacyStatus": "private",            # obrigatório para usar publishAt
            "publishAt": meta.publish_at,
            "selfDeclaredMadeForKids": meta.made_for_kids,
            "containsSyntheticMedia": meta.contains_synthetic_media,
        },
    }


def load_credentials():
    """Credenciais OAuth do dono do canal, sem nunca tocar no repositório."""
    from google.oauth2.credentials import Credentials

    env = {k: os.getenv(k) for k in ("YT_CLIENT_ID", "YT_CLIENT_SECRET", "YT_REFRESH_TOKEN")}
    if not all(env.values()):
        if not os.path.exists(LOCAL_CREDENTIALS):
            raise RuntimeError("Credenciais do YouTube ausentes: defina YT_CLIENT_ID, YT_CLIENT_SECRET e "
                               "YT_REFRESH_TOKEN ou rode python -m scripts.youtube_auth")
        mode = stat.S_IMODE(os.stat(LOCAL_CREDENTIALS).st_mode)
        if mode & 0o077:
            raise RuntimeError(f"{LOCAL_CREDENTIALS} está acessível a outros usuários; rode chmod 600")
        with open(LOCAL_CREDENTIALS, encoding="utf-8") as f:
            data = json.load(f)
        env = {"YT_CLIENT_ID": data["client_id"], "YT_CLIENT_SECRET": data["client_secret"],
               "YT_REFRESH_TOKEN": data["refresh_token"]}
    return Credentials(token=None, refresh_token=env["YT_REFRESH_TOKEN"], client_id=env["YT_CLIENT_ID"],
                       client_secret=env["YT_CLIENT_SECRET"], token_uri=TOKEN_URI, scopes=SCOPES)


class YouTubePublisher:
    def __init__(self, youtube=None, sleep=time.sleep):
        self._youtube = youtube
        self._sleep = sleep

    @property
    def youtube(self):
        if self._youtube is None:
            from googleapiclient.discovery import build
            self._youtube = build("youtube", "v3", credentials=load_credentials(), cache_discovery=False)
        return self._youtube

    def upload(self, video_path: str, meta: PublishMetadata, thumbnail_path: Optional[str] = None,
               dry_run: bool = False) -> dict:
        if not os.path.isfile(video_path):
            raise FileNotFoundError(video_path)
        body = build_body(meta)
        if dry_run:
            return {"dry_run": True, "body": body, "video_path": video_path}

        from googleapiclient.errors import HttpError
        from googleapiclient.http import MediaFileUpload

        media = MediaFileUpload(video_path, mimetype="video/*", chunksize=8 * 1024 * 1024, resumable=True)
        request = self.youtube.videos().insert(part="snippet,status", body=body, media_body=media)
        response, attempt = None, 0
        while response is None:
            try:
                _, response = request.next_chunk()
            except HttpError as e:
                status = getattr(e.resp, "status", None)
                if status not in RETRIABLE_STATUS:
                    raise                                # 4xx: quota, escopo, auditoria → não insiste
                attempt = self._backoff(attempt, f"HTTP {status}")
            except (ConnectionError, TimeoutError, OSError) as e:
                attempt = self._backoff(attempt, type(e).__name__)
        video_id = response["id"]

        result = {"video_id": video_id, "publish_at": meta.publish_at,
                  "privacy": "private", "url": f"https://youtu.be/{video_id}"}
        if thumbnail_path and os.path.isfile(thumbnail_path):
            self.youtube.thumbnails().set(
                videoId=video_id, media_body=MediaFileUpload(thumbnail_path, mimetype="image/jpeg")).execute()
            result["thumbnail"] = os.path.basename(thumbnail_path)
        return result

    def _backoff(self, attempt: int, reason: str) -> int:
        attempt += 1
        if attempt > MAX_RETRIES:
            raise RuntimeError(f"upload falhou após {MAX_RETRIES} tentativas ({reason})")
        self._sleep(min(2 ** attempt + random.random(), 64))
        return attempt
