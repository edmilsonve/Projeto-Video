"""Log estruturado (JSON Lines) com mascaramento de segredos.

Cada evento vira uma linha em logs/<AAAA-MM-DD>.jsonl. Valores que parecem
credenciais são mascarados antes de gravar, para que um log nunca vaze uma chave.
"""
import json
import os
import re
from datetime import datetime, timezone

LOG_DIR = os.getenv("DARKSTUDIO_LOG_DIR", "logs")

_SECRET_PATTERNS = [
    re.compile(r"sk-ant-[A-Za-z0-9_\-]{10,}"),
    re.compile(r"AIza[0-9A-Za-z_\-]{30,}"),
    re.compile(r"GOCSPX-[A-Za-z0-9_\-]{10,}"),
    re.compile(r"1//0[A-Za-z0-9_\-]{20,}"),
    re.compile(r"ya29\.[A-Za-z0-9_\-]{20,}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"r8_[A-Za-z0-9]{20,}"),
]
_SECRET_KEYS = re.compile(r"(key|token|secret|password|authorization|credential)", re.I)


def redact(value):
    """Mascara segredos em strings, dicts e listas (recursivo)."""
    if isinstance(value, dict):
        return {k: ("***" if _SECRET_KEYS.search(str(k)) and isinstance(v, str) and v else redact(v))
                for k, v in value.items()}
    if isinstance(value, list):
        return [redact(v) for v in value]
    if isinstance(value, str):
        for pattern in _SECRET_PATTERNS:
            value = pattern.sub("***", value)
    return value


def log_event(agent: str, step: str, status: str, run_id: str = None, **fields) -> dict:
    """Grava um evento estruturado e o devolve (já mascarado)."""
    event = {"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
             "run_id": run_id, "agent": agent, "step": step, "status": status}
    event.update(redact(fields))
    os.makedirs(LOG_DIR, exist_ok=True)
    path = os.path.join(LOG_DIR, f"{event['ts'][:10]}.jsonl")
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
    return event
