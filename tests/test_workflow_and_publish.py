"""Workflow, documentação gerada, publicação no YouTube e varredura de segredos (sem rede)."""
import json
import os
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from core.workflow import Run, WorkflowError, find_runs
from scripts import check_secrets, gen_workflow_docs
from scripts.publish import publish_run
from services.youtube_publisher import PublishMetadata, YouTubePublisher, build_body


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("utils.log.LOG_DIR", str(tmp_path / "logs"))


def future(hours=48):
    return (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat()


def meta(**kw):
    base = dict(title="A história do café", publish_at=future(), contains_synthetic_media=True,
                video_file="cafe.mp4", thumbnail_file="thumb_a.jpg")
    base.update(kw)
    return base


# --- Workflow -----------------------------------------------------------------
def test_happy_path_records_events():
    run = Run.create("runs/cafe-01", "café")
    run.transition("failed", actor="pipeline", note="timeout")
    run.transition("draft", actor="pipeline", note="retry")  # volta à etapa de origem
    open("runs/cafe-01/brief.yaml", "w").close()
    run.transition("grilled", actor="pipeline")
    events = [json.loads(line) for line in open("runs/cafe-01/events.jsonl")]
    assert [e["to"] for e in events] == ["draft", "failed", "draft", "grilled"]
    assert os.listdir("logs")  # também foi para o log global


def test_illegal_transition_and_missing_artifacts():
    run = Run.create("runs/cafe-02", "café")
    with pytest.raises(WorkflowError, match="proibida"):
        run.transition("published", actor="pipeline")
    with pytest.raises(WorkflowError, match="faltam artefatos"):
        run.transition("grilled", actor="pipeline")  # brief.yaml ausente


def test_human_gate_rejects_agents():
    run = Run.create("runs/cafe-03", "café")
    data = run.read()
    data["state"] = "pr_open"
    run._write(data)
    with pytest.raises(WorkflowError, match="aprovação humana"):
        run.transition("approved", actor="pipeline")
    run.transition("approved", actor="human:edmilson")
    assert run.state == "approved"


@pytest.mark.parametrize("bad", ["../etc", "Runs_X", "a"])
def test_run_id_is_validated(bad):
    with pytest.raises(WorkflowError):
        Run(f"runs/{bad}")


def test_workflow_doc_is_in_sync():
    path = gen_workflow_docs.DOC_PATH
    assert open(path, encoding="utf-8").read() == gen_workflow_docs.render(), \
        "rode python scripts/gen_workflow_docs.py"


# --- YouTube ------------------------------------------------------------------
def test_body_is_private_scheduled_and_disclosed():
    body = build_body(PublishMetadata(**meta()))
    assert body["status"]["privacyStatus"] == "private"
    assert body["status"]["containsSyntheticMedia"] is True
    assert body["status"]["publishAt"].endswith("Z")


@pytest.mark.parametrize("bad", [dict(publish_at="2020-01-01T00:00:00+00:00"),
                                 dict(publish_at="2030-01-01T10:00:00"),
                                 dict(title="x" * 101), dict(title="<script>"),
                                 dict(tags=["t" * 300, "u" * 300])])
def test_metadata_validation(bad):
    with pytest.raises(ValueError):
        PublishMetadata(**meta(**bad))


def test_synthetic_disclosure_is_mandatory():
    data = meta()
    data.pop("contains_synthetic_media")
    with pytest.raises(ValueError):
        PublishMetadata(**data)


class FakeYouTube:
    def __init__(self):
        self.inserted, self.thumbs = [], []

    def videos(self):
        outer = self

        class Videos:
            def insert(self, **kw):
                outer.inserted.append(kw)
                return SimpleNamespace(next_chunk=lambda: (None, {"id": "vid123"}))
        return Videos()

    def thumbnails(self):
        outer = self

        class Thumbs:
            def set(self, **kw):
                outer.thumbs.append(kw)
                return SimpleNamespace(execute=lambda: {})
        return Thumbs()


def make_pr_open_run(tmp_dir="runs/cafe-10"):
    run = Run.create(tmp_dir, "café")
    data = run.read()
    data["state"] = "pr_open"
    run._write(data)
    json.dump(meta(), open(f"{tmp_dir}/metadata.json", "w"))
    open(f"{tmp_dir}/thumb_a.jpg", "wb").write(b"jpg")
    os.makedirs("final_videos", exist_ok=True)
    open("final_videos/cafe.mp4", "wb").write(b"mp4")
    return run


def test_publish_run_schedules_and_records(monkeypatch):
    monkeypatch.setattr("scripts.publish.LOCAL_VIDEO_DIR", "final_videos")
    run = make_pr_open_run()
    yt = FakeYouTube()
    result = publish_run(run, "edmilson", YouTubePublisher(youtube=yt))
    assert result["video_id"] == "vid123" and run.state == "scheduled"
    assert yt.inserted[0]["body"]["status"]["privacyStatus"] == "private"
    assert yt.thumbs and json.load(open("runs/cafe-10/youtube.json"))["url"].endswith("vid123")
    actors = [json.loads(line)["actor"] for line in open("runs/cafe-10/events.jsonl")]
    assert "human:edmilson" in actors


def test_publish_refuses_runs_not_merged(monkeypatch):
    run = Run.create("runs/cafe-11", "café")
    with pytest.raises(WorkflowError, match="pr_open"):
        publish_run(run, "edmilson", YouTubePublisher(youtube=FakeYouTube()))


def test_dry_run_does_not_upload_or_change_state(monkeypatch):
    monkeypatch.setattr("scripts.publish.LOCAL_VIDEO_DIR", "final_videos")
    run = make_pr_open_run("runs/cafe-12")
    yt = FakeYouTube()
    assert publish_run(run, "edmilson", YouTubePublisher(youtube=yt), dry_run=True)["dry_run"]
    assert not yt.inserted and run.state == "pr_open"
    assert [r.run_id for r in find_runs(state="pr_open")] == ["cafe-12"]


def test_ci_mode_requires_github_actions(monkeypatch):
    from scripts.publish import main
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    with pytest.raises(SystemExit):
        main(["--ci", "--pending"])


# --- Segredos -----------------------------------------------------------------
def test_secret_scanner_detects_without_printing_value():
    fake_key = "sk-" + "ant-" + "a" * 30  # montado em tempo de execução para não acionar o próprio scanner
    files = {"app.py": f"KEY = '{fake_key}'", "ok.py": "KEY = os.getenv('ANTHROPIC_API_KEY')",
             "client_secret_123.json": "{}", ".env.example": "ANTHROPIC_API_KEY=your_anthropic_key"}
    findings = check_secrets.scan(files, read=files.__getitem__)
    assert ("app.py", 1, "Anthropic API key") in findings
    assert ("client_secret_123.json", 0, "arquivo de credencial versionado") in findings
    assert not [f for f in findings if f[0] in ("ok.py", ".env.example")]


def test_log_redacts_secrets():
    from utils.log import log_event, redact
    token = "1//0" + "x" * 40
    assert redact({"refresh_token": token, "note": f"t={token}"}) == {"refresh_token": "***", "note": "t=***"}
    assert "***" in log_event("t", "s", "ok", detail=token)["detail"]
