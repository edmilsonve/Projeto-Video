"""Máquina de estados do vídeo: fonte única da verdade do workflow.

- Os estados, quem move cada um e os artefatos esperados ficam declarados em STATES.
- As transições permitidas ficam em TRANSITIONS; qualquer outra é recusada.
- Cada transição grava runs/<id>/state.json e acrescenta uma linha em runs/<id>/events.jsonl.
- docs/WORKFLOW.md é GERADO a partir daqui (scripts/gen_workflow_docs.py); o CI recusa
  o PR se o documento estiver desatualizado. Assim a documentação nunca diverge do código.
"""
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone

from utils.log import log_event

RUN_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{2,80}$")


@dataclass(frozen=True)
class StateInfo:
    description: str
    owner: str          # quem tira o vídeo deste estado
    artifacts: tuple    # o que precisa existir em runs/<id>/ para ENTRAR nele


STATES = {
    "draft": StateInfo("Tema recebido", "pipeline (Grill)", ()),
    "grilled": StateInfo("Brief aprovado pela pessoa no Grill", "pipeline", ("brief.yaml",)),
    "researched": StateInfo("Pesquisa, outliers e SEO prontos", "pipeline", ("research.md", "outliers.csv")),
    "scripted": StateInfo("Roteiro gerado (Claude → Gemini)", "pipeline (Revisor)", ("script.json",)),
    "reviewed": StateInfo("Fatos, humanização e compliance verificados", "humano", ("review.json", "script.final.json")),
    "script_approved": StateInfo("Roteiro aprovado pela pessoa", "pipeline (mídia)", ()),
    "produced": StateInfo("Voz, imagens, edição, legendas e thumbs prontos", "pipeline (QA)", ("thumb_a.jpg",)),
    "qa_passed": StateInfo("QA automático aprovado", "pipeline (abre PR)", ("qa.json", "metadata.json")),
    "pr_open": StateInfo("PR aberto aguardando revisão humana", "humano (merge) + ambiente youtube-production", ()),
    "approved": StateInfo("Merge feito e publicação aprovada no ambiente protegido", "CI publish", ()),
    "scheduled": StateInfo("Enviado ao YouTube como privado com publishAt", "YouTube", ("youtube.json",)),
    "published": StateInfo("Público no YouTube", "pipeline (Analista)", ()),
    "analyzed": StateInfo("Métricas de 48 h, 7 d e 28 d registradas", "pipeline", ("report.md",)),
    "archived": StateInfo("Encerrado", "—", ()),
    "failed": StateInfo("Etapa falhou após as retentativas; volta à etapa de origem", "pipeline ou humano", ()),
}

TRANSITIONS = {
    "draft": ("grilled",),
    "grilled": ("researched",),
    "researched": ("scripted",),
    "scripted": ("reviewed",),
    "reviewed": ("script_approved", "scripted"),       # aprovar ou pedir nova versão
    "script_approved": ("produced",),
    "produced": ("qa_passed", "produced"),             # QA reprovado refaz a produção
    "qa_passed": ("pr_open",),
    "pr_open": ("approved", "script_approved"),        # aprovado, ou mudanças pedidas no PR
    "approved": ("scheduled",),
    "scheduled": ("published",),
    "published": ("analyzed",),
    "analyzed": ("archived",),
    "archived": (),
    "failed": (),                                      # só volta para failed_from (ver transition)
}

# Transições que só uma pessoa pode autorizar (o actor precisa começar com "human:").
HUMAN_GATES = {("reviewed", "script_approved"), ("pr_open", "approved")}
TERMINAL = {"archived"}


class WorkflowError(Exception):
    pass


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Run:
    def __init__(self, run_dir: str):
        parts = run_dir.replace("\\", "/").rstrip("/").split("/")
        run_id = parts[-1]
        if ".." in parts or not RUN_ID_RE.match(run_id):
            raise WorkflowError(f"run_id inválido: {run_id!r} (use letras minúsculas, números e '-')")
        self.run_id, self.dir = run_id, run_dir
        self.state_path = os.path.join(run_dir, "state.json")
        self.events_path = os.path.join(run_dir, "events.jsonl")

    @classmethod
    def create(cls, run_dir: str, topic: str, actor: str = "pipeline"):
        run = cls(run_dir)
        if os.path.exists(run.state_path):
            raise WorkflowError(f"run já existe: {run.run_id}")
        os.makedirs(run_dir, exist_ok=True)
        run._write({"run_id": run.run_id, "topic": topic, "state": "draft", "updated_at": _now()})
        run._append_event(None, "draft", actor, "criado")
        return run

    def read(self) -> dict:
        if not os.path.exists(self.state_path):
            raise WorkflowError(f"run sem state.json: {self.run_id}")
        with open(self.state_path, encoding="utf-8") as f:
            return json.load(f)

    @property
    def state(self) -> str:
        return self.read()["state"]

    def can(self, target: str) -> bool:
        data = self.read()
        if data["state"] == "failed":
            return target in (data.get("failed_from"), "archived")
        return (target == "failed" and data["state"] not in TERMINAL) or target in TRANSITIONS[data["state"]]

    def transition(self, target: str, actor: str, note: str = "", **extra) -> dict:
        if target not in STATES:
            raise WorkflowError(f"estado desconhecido: {target}")
        data = self.read()
        current = data["state"]
        if not self.can(target):
            raise WorkflowError(f"transição proibida: {current} → {target}")
        if (current, target) in HUMAN_GATES and not actor.startswith("human:"):
            raise WorkflowError(f"{current} → {target} exige aprovação humana (actor='human:<nome>')")
        missing = [a for a in STATES[target].artifacts if not os.path.exists(os.path.join(self.dir, a))]
        if missing:
            raise WorkflowError(f"faltam artefatos para entrar em {target}: {missing}")
        if target == "failed":
            data["failed_from"] = current
        elif current == "failed":
            data.pop("failed_from", None)
        data.update(extra, state=target, updated_at=_now())
        self._write(data)
        self._append_event(current, target, actor, note)
        return data

    def _write(self, data):
        tmp = self.state_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)
        os.replace(tmp, self.state_path)  # escrita atômica

    def _append_event(self, src, dst, actor, note):
        event = {"ts": _now(), "run_id": self.run_id, "from": src, "to": dst, "actor": actor, "note": note}
        with open(self.events_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
        log_event("workflow", f"{src}->{dst}", "ok", run_id=self.run_id, actor=actor, note=note)


def find_runs(root: str = "runs", state: str = None):
    """Lista os runs (opcionalmente filtrando por estado)."""
    if not os.path.isdir(root):
        return []
    runs = []
    for name in sorted(os.listdir(root)):
        path = os.path.join(root, name)
        if os.path.isfile(os.path.join(path, "state.json")) and RUN_ID_RE.match(name):
            run = Run(path)
            if state is None or run.state == state:
                runs.append(run)
    return runs
