"""Publica no YouTube os runs aprovados. Só uma PESSOA dispara este comando.

CI (recomendado; roda no ambiente protegido youtube-production, depois da aprovação):
    python -m scripts.publish --ci --pending
    python -m scripts.publish --ci --run runs/<id>
Local (alternativa; no seu terminal, nunca pelo agente):
    python -m scripts.publish --run runs/<id> --approved-by "Seu Nome" [--dry-run]

Regras:
- Só publica runs no estado pr_open (o PR já passou por merge). A transição para
  approved registra quem aprovou; depois o vídeo sobe como privado com publishAt (scheduled).
- O vídeo vem de final_videos/<video_file> ou, se não existir, da pasta do Drive.
"""
import argparse
import getpass
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.workflow import Run, WorkflowError, find_runs  # noqa: E402
from services.youtube_publisher import PublishMetadata, YouTubePublisher  # noqa: E402
from utils.log import log_event  # noqa: E402

LOCAL_VIDEO_DIR = os.getenv("DARKSTUDIO_VIDEO_DIR", "final_videos")


def resolve_video(meta: PublishMetadata, workdir: str, drive=None) -> str:
    local = os.path.join(LOCAL_VIDEO_DIR, meta.video_file)
    if os.path.isfile(local):
        return local
    if drive is None:
        from storage.drive import DriveService
        drive = DriveService(readonly=True)
    found = drive.find_file(meta.video_file)
    if not found:
        raise FileNotFoundError(f"{meta.video_file} não está em {LOCAL_VIDEO_DIR}/ nem na pasta do Drive")
    return drive.download_file(found["id"], os.path.join(workdir, os.path.basename(meta.video_file)))


def publish_run(run: Run, approver: str, publisher: YouTubePublisher, dry_run=False, drive=None) -> dict:
    if run.state != "pr_open":
        raise WorkflowError(f"{run.run_id}: estado {run.state!r}; só runs em pr_open (PR com merge) são publicados")
    with open(os.path.join(run.dir, "metadata.json"), encoding="utf-8") as f:
        meta = PublishMetadata.model_validate(json.load(f))
    thumb = os.path.join(run.dir, meta.thumbnail_file) if meta.thumbnail_file else None

    with tempfile.TemporaryDirectory() as workdir:
        video = resolve_video(meta, workdir, drive)
        if dry_run:
            result = publisher.upload(video, meta, thumb, dry_run=True)
            log_event("publisher", "dry_run", "ok", run_id=run.run_id, title=meta.title)
            return result
        run.transition("approved", actor=f"human:{approver}", note="merge do PR + aprovação da publicação")
        try:
            result = publisher.upload(video, meta, thumb)
        except Exception as e:
            run.transition("failed", actor="publisher", note=f"upload: {type(e).__name__}")
            log_event("publisher", "upload", "error", run_id=run.run_id, error=str(e)[:300])
            raise
    with open(os.path.join(run.dir, "youtube.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, sort_keys=True)
    run.transition("scheduled", actor="publisher", note=result["url"], video_id=result["video_id"])
    log_event("publisher", "upload", "ok", run_id=run.run_id, video_id=result["video_id"],
              publish_at=result["publish_at"])
    return result


def main(argv=None):
    parser = argparse.ArgumentParser()
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--run", help="pasta do run, ex.: runs/2026-11-10-cafe")
    target.add_argument("--pending", action="store_true", help="todos os runs em pr_open")
    parser.add_argument("--ci", action="store_true", help="modo GitHub Actions (aprovador = APPROVER)")
    parser.add_argument("--approved-by", help="seu nome (modo local)")
    parser.add_argument("--dry-run", action="store_true", help="valida tudo sem enviar")
    args = parser.parse_args(argv)

    if args.ci:
        if os.getenv("GITHUB_ACTIONS") != "true":
            parser.error("--ci só roda dentro do GitHub Actions")
        approver = f"github:{os.environ['APPROVER']}"
    else:
        if not args.approved_by:
            parser.error("informe --approved-by no modo local")
        approver = args.approved_by

    runs = find_runs(state="pr_open") if args.pending else [Run(args.run)]
    if not runs:
        print("Nenhum run pendente de publicação.")
        return 0
    if not args.ci and not args.dry_run:
        titles = ", ".join(r.run_id for r in runs)
        answer = input(f"{getpass.getuser()}, publicar {titles}? Digite PUBLICAR para confirmar: ")
        if answer.strip() != "PUBLICAR":
            print("Cancelado.")
            return 1

    publisher, failures = YouTubePublisher(), 0
    for run in runs:
        try:
            result = publish_run(run, approver, publisher, dry_run=args.dry_run)
            print(f"{run.run_id}: {result.get('url', 'dry-run ok')}")
        except Exception as e:
            failures += 1
            print(f"{run.run_id}: FALHOU ({type(e).__name__}: {e})")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
