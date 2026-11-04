"""Gera docs/WORKFLOW.md a partir de core/workflow.py.

Uso:  python scripts/gen_workflow_docs.py          # regrava o documento
      python scripts/gen_workflow_docs.py --check  # falha se estiver desatualizado (CI)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.workflow import HUMAN_GATES, STATES, TRANSITIONS  # noqa: E402

DOC_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "WORKFLOW.md")


def render() -> str:
    lines = [
        "# Workflow do vídeo (gerado automaticamente)",
        "",
        "> Não edite à mão: este arquivo é gerado de `core/workflow.py` por "
        "`python scripts/gen_workflow_docs.py`. O CI recusa o PR se ele estiver desatualizado.",
        "",
        "```mermaid",
        "stateDiagram-v2",
        "    [*] --> draft",
    ]
    for src, targets in TRANSITIONS.items():
        for dst in targets:
            label = " : humano" if (src, dst) in HUMAN_GATES else ""
            lines.append(f"    {src} --> {dst}{label}")
    lines += ["    archived --> [*]", "    note right of failed : qualquer estado não terminal pode ir para failed e voltar à etapa de origem", "```", "",
              "| Estado | Significado | Quem tira o vídeo daqui | Artefatos exigidos para entrar | Próximos estados |",
              "|---|---|---|---|---|"]
    for name, info in STATES.items():
        arts = ", ".join(f"`{a}`" for a in info.artifacts) or "—"
        nxt = ", ".join(f"`{t}`" for t in TRANSITIONS[name]) or ("`failed_from`, `archived`" if name == "failed" else "—")
        lines.append(f"| `{name}` | {info.description} | {info.owner} | {arts} | {nxt} |")
    gates = ", ".join(f"`{a} → {b}`" for a, b in sorted(HUMAN_GATES))
    lines += ["", f"**Portões humanos** (o actor precisa ser `human:<nome>`): {gates}.", "",
              "**Registro:** cada transição grava `runs/<id>/state.json` (escrita atômica) e acrescenta uma linha "
              "em `runs/<id>/events.jsonl` e em `logs/<data>.jsonl` (`{ts, run_id, from, to, actor, note}`).", ""]
    return "\n".join(lines)


def main():
    content = render()
    if "--check" in sys.argv:
        current = open(DOC_PATH, encoding="utf-8").read() if os.path.exists(DOC_PATH) else ""
        if current != content:
            print("docs/WORKFLOW.md desatualizado: rode python scripts/gen_workflow_docs.py")
            sys.exit(1)
        print("docs/WORKFLOW.md em dia.")
        return
    with open(DOC_PATH, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Gerado {DOC_PATH}")


if __name__ == "__main__":
    main()
