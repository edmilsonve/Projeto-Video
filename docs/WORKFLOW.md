# Workflow do vídeo (gerado automaticamente)

> Não edite à mão: este arquivo é gerado de `core/workflow.py` por `python scripts/gen_workflow_docs.py`. O CI recusa o PR se ele estiver desatualizado.

```mermaid
stateDiagram-v2
    [*] --> draft
    draft --> grilled
    grilled --> researched
    researched --> scripted
    scripted --> reviewed
    reviewed --> script_approved : humano
    reviewed --> scripted
    script_approved --> produced
    produced --> qa_passed
    produced --> produced
    qa_passed --> pr_open
    pr_open --> approved : humano
    pr_open --> script_approved
    approved --> scheduled
    scheduled --> published
    published --> analyzed
    analyzed --> archived
    archived --> [*]
    note right of failed : qualquer estado não terminal pode ir para failed e voltar à etapa de origem
```

| Estado | Significado | Quem tira o vídeo daqui | Artefatos exigidos para entrar | Próximos estados |
|---|---|---|---|---|
| `draft` | Tema recebido | pipeline (Grill) | — | `grilled` |
| `grilled` | Brief aprovado pela pessoa no Grill | pipeline | `brief.yaml` | `researched` |
| `researched` | Pesquisa, outliers e SEO prontos | pipeline | `research.md`, `outliers.csv` | `scripted` |
| `scripted` | Roteiro gerado (Claude → Gemini) | pipeline (Revisor) | `script.json` | `reviewed` |
| `reviewed` | Fatos, humanização e compliance verificados | humano | `review.json`, `script.final.json` | `script_approved`, `scripted` |
| `script_approved` | Roteiro aprovado pela pessoa | pipeline (mídia) | — | `produced` |
| `produced` | Voz, imagens, edição, legendas e thumbs prontos | pipeline (QA) | `thumb_a.jpg` | `qa_passed`, `produced` |
| `qa_passed` | QA automático aprovado | pipeline (abre PR) | `qa.json`, `metadata.json` | `pr_open` |
| `pr_open` | PR aberto aguardando revisão humana | humano (merge) + ambiente youtube-production | — | `approved`, `script_approved` |
| `approved` | Merge feito e publicação aprovada no ambiente protegido | CI publish | — | `scheduled` |
| `scheduled` | Enviado ao YouTube como privado com publishAt | YouTube | `youtube.json` | `published` |
| `published` | Público no YouTube | pipeline (Analista) | — | `analyzed` |
| `analyzed` | Métricas de 48 h, 7 d e 28 d registradas | pipeline | `report.md` | `archived` |
| `archived` | Encerrado | — | — | — |
| `failed` | Etapa falhou após as retentativas; volta à etapa de origem | pipeline ou humano | — | `failed_from`, `archived` |

**Portões humanos** (o actor precisa ser `human:<nome>`): `pr_open → approved`, `reviewed → script_approved`.

**Registro:** cada transição grava `runs/<id>/state.json` (escrita atômica) e acrescenta uma linha em `runs/<id>/events.jsonl` e em `logs/<data>.jsonl` (`{ts, run_id, from, to, actor, note}`).
