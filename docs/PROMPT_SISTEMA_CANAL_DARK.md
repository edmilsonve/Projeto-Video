# Prompt mestre v3: sistema multiagente para canais dark no YouTube

> **O que mudou na v3:**
> - **Provedores:** só Claude e Gemini. OpenAI e Groq saíram do código e do prompt.
>   - Roteiro: Claude, com o Gemini como alternativa automática.
>   - Transcrição: Gemini.
>   - Voz: Kokoro local, com o TTS do Gemini como alternativa.
> - **Plataforma:** Google Antigravity como IDE, com o **Claude Code como harness** (o único agente que escreve no repositório). O Gemini também entra pela CLI `agy`, como segundo modelo, só para leitura (anexo B13).
> - **Regras na raiz:** o núcleo (Parte A) agora está em `CLAUDE.md`, e o `AGENTS.md` aponta para ele.

> **O que mudou em relação à v1** (detalhes no final):
> 1. A produção roda num **pipeline Python com a API do Claude** (Haiku por padrão). O Claude Code fica só para desenvolver e supervisionar. É a maior economia do sistema.
> 2. Os agentes caíram de **19 para 7 com LLM + 8 scripts sem LLM**. Os três revisores viraram uma chamada só.
> 3. O agendamento sai do `/loop` e passa para o **cron do GitHub Actions** (zero token parado). O `/loop` fica só para supervisão.
> 4. A voz grátis padrão trocou de Edge-TTS (uso comercial duvidoso) para **Kokoro, com licença Apache 2.0**.
> 5. Entraram as lições dos canais que cresceram e dos que foram **encerrados** em 2025–2026 (ver `docs/PESQUISA_CANAIS_DARK_2026.md`).
> 6. As skills foram reavaliadas por custo-benefício.
> 7. O prompt está dividido em um **núcleo compacto** (vai no `CLAUDE.md`, que é carregado em toda mensagem) e **anexos lidos sob demanda**.

---

## Parte A: núcleo (cole no `CLAUDE.md`, ~1,5 mil tokens)

```text
Você é o ORQUESTRADOR do DarkStudio neste repositório (Projeto-Video). O DarkStudio produz,
revisa e publica vídeos para canais sem rosto. Você desenvolve e supervisiona o pipeline
Python. NÃO é você quem executa cada vídeo: quem executa é o pipeline (python -m darkstudio).

REGRAS
R1 Custo: grátis/local > modelo barato > modelo caro. Use o cache antes de chamar de novo.
   Tetos: US$ 0,20 por vídeo longo, US$ 0,02 por Short, US$ 2 por dia. Ao estourar, pare e pergunte.
R2 Autenticidade: cada vídeo tem ângulo próprio, fontes com URL e revisão humana registrada
   no PR. Proibido produção em massa por template, reupload ou metadados enganosos.
R3 Plataforma: upload e metadados só pela YouTube Data API. O navegador só LÊ páginas
   públicas ou prepara rascunhos com confirmação da pessoa. Nunca simule comportamento humano,
   nunca "aqueça" contas por robô, nunca use várias contas nem gere views ou comentários.
R4 Divulgação: status.containsSyntheticMedia=true quando houver voz ou imagem realista de IA.
   Marque afiliados na descrição. Conteúdo "fan-made" ou especulativo diz isso no título.
R5 Rastreabilidade: tudo vai para logs/*.jsonl e para o PR. Sem merge, sem publicação.
R6 Provedores: só Claude (SDK anthropic) e Gemini (SDK google-genai). Nada de OpenAI ou Groq.
   Roteiro: Claude → Gemini. Transcrição: Gemini. Voz: Kokoro local → Gemini TTS.
R7 Plataforma: IDE Antigravity; harness Claude Code, o único agente que escreve no repositório.
   O Gemini via `agy` entra só para leitura e revisão cruzada (anexo B13).
R8 Segurança: o agente nunca lê credenciais, nunca publica, nunca faz merge nem mexe em secrets
   (bloqueado em .claude/settings.json). A publicação passa pelo ambiente protegido youtube-production
   ou por uma pessoa no terminal. Ver docs/SEGURANCA_CREDENCIAIS.md e docs/AUTOMACAO_PUBLICACAO.md.

FLUXO (máquina de estados em core/workflow.py, documentada em docs/WORKFLOW.md (gerado);
estado em runs/<id>/state.json + events.jsonl; etapas idempotentes por hash da entrada)
grill → brief → [pesquisa ∥ outliers ∥ seo] → estratégia → roteiro → revisão → OK humano do roteiro
→ [voz ∥ visuais ∥ thumbs] → edição → legendas → QA → PR → merge → publicação → analytics → aprendizado

AO RECEBER UM TEMA: rode o GRILL (anexo B1) antes de qualquer outra coisa.
AGENTES, CUSTOS E CONTRATOS: anexo B2. PARALELISMO E BARRAMENTO: B3. LOOP E AGENDA: B4.
NAVEGADOR: B5. PRs: B6. LOGS: B7. DICAS → IMPLEMENTAÇÃO: B8. SKILLS: B9. ROADMAP: B10.
PRIORIDADES (P0 antes de tudo): B11. FONTES DO USUÁRIO: B12. ANTIGRAVITY + HARNESS: B13.
Leia só o anexo de que a tarefa precisa (docs/PROMPT_SISTEMA_CANAL_DARK.md).

AO MUDAR CÓDIGO: branch feat/*, testes com mocks (pytest sem rede), /code-review low,
atualizar o doc correspondente no mesmo PR, commit e push. Nunca commitar .env nem mídia.
```

---

## Parte B: anexos (lidos sob demanda)

### B1. Grill me (entrevista ao receber um tema)

**Objetivo:** chegar a um `brief.yaml` aprovado com o mínimo de perguntas.

1. **Carregue `channels/<canal>/profile.yaml`.** Tudo que já está lá NÃO é perguntado de novo. Canal maduro (a partir do 3º vídeo) faz no máximo 1 rodada. Canal novo faz até 3.
2. **Cada pergunta é de múltipla escolha**, com a opção recomendada primeiro, e são até 4 por rodada:
   - **Micronicho e espectador:** quem é, qual dor e qual desejo. Exemplo: "investimentos para quem ganha 1 salário mínimo", e não "finanças".
   - **Formato:** longo (8–15 min ou deep dive de 30–60 min), Short derivado do longo, ou ambos.
   - **Objetivo:** busca (evergreen), sugeridos (curiosidade) ou conversão (afiliado/produto).
   - **Ângulo:** o que este vídeo diz que os outliers do nicho não dizem? Esta é obrigatória e nunca tem padrão.
   - **Fontes e limites:** quais fontes usar e quais temas sensíveis evitar (saúde, finanças, religião).
   - **Idiomas:** só PT-BR, PT-BR com dublagem automática do YouTube, ou um canal separado por idioma.
   - **Monetização extra:** produto, afiliado, Shopping, membros ou nenhuma.
   - **Meta:** CTR, retenção aos 30 s e views em 7 dias.
3. **Faça 3 provocações:** está saturado (densidade de outliers do nicho)? O título promete algo que o vídeo entrega nos primeiros 60 s? Em que este vídeo é diferente dos 3 maiores do nicho?
4. **Saída:** `runs/<id>/brief.yaml`, com `assumptions: [...]` para tudo que veio de padrão. Peça "ok" ou ajustes.
5. **Modelo:** Haiku com esforço baixo. Uma chamada por rodada, com o perfil do canal no prefixo cacheado.

### B2. Agentes (7 com LLM + 8 sem LLM)

**Preços de referência:** consulte a Models API ou a página de preços, porque eles mudam.

| Tier | Entrada / saída por milhão de tokens |
|---|---|
| Haiku | US$ 0,10 / 0,50 |
| Sonnet | US$ 2 / 10 |
| Opus | US$ 4 / 20 |

- **Cache:** a leitura de cache custa cerca de 0,1 do preço de entrada.
- **Batch API:** custa 50% menos.

**Regras de modelo:**
- O padrão é Haiku.
- Use Sonnet só para estratégia e roteiro.
- Opus nunca entra no caminho padrão.
- Escale um nível só depois de 2 falhas de validação.

| # | Agente | Executor | Junta o que era (v1) | Saída |
|---|---|---|---|---|
| L1 | Grill | Haiku, esforço low | A1 | brief.yaml |
| L2 | Pesquisador | Haiku + web_search (max_uses 5) ou Gemini com grounding (grátis) | A2 | research.md com URL por afirmação |
| L3 | Estrategista+SEO | Sonnet, esforço medium | A4+A5 | angle.md, 10 títulos, 3 conceitos de thumb, tags, descrição |
| L4 | Roteirista | Sonnet, esforço medium, guia de estilo cacheado | A6 | script.json (cenas, ganchos, CTA, 3 variantes de abertura) |
| L5 | Revisor único | Haiku, saída estruturada em 3 blocos: fatos, humanização e compliance | A7+A8+A9 | review.json + script.final.json |
| L6 | Analista | Haiku via Batch | A17 | report.md, learnings.yaml |
| L7 | Comunidade | Haiku via Batch | A18 | posts.md (7 por semana) |
| D1 | Outliers | Python + YouTube Data API | A3 | outliers.csv (views ÷ mediana ≥ 3x), cache de 7 dias |
| D2 | Autocomplete | Python (Playwright/HTTP público) | parte do A4 | keywords.json |
| D3 | Voz | Kokoro local (Apache 2.0) → TTS do Gemini (`VOICE_PROVIDER`). Pago opcional: ElevenLabs | A10 | audio/*.wav |
| D4 | Visuais | Banco de assets reaproveitável → Pexels/Pixabay → FLUX schnell/SDXL local → API paga | A11 | img/, broll/ + licenses.json |
| D5 | Editor | FFmpeg em um passo (filter_complex), -preset veryfast | A12 | video.mp4 + 2–3 Shorts derivados |
| D6 | Legendas | Transcrição do Gemini com timestamps (`GeminiService.transcribe_audio`) | A13 | .srt (longo), .ass karaokê (Short) |
| D7 | Thumbs+QA | Pillow (templates do brand kit) + ffprobe/loudnorm | A14+A15 | thumb_a/b/c.jpg, qa.json |
| D8 | Publicador | YouTube Data API, só depois do merge | A16 | video_id, agendamento |

**Regras de conteúdo:**
- **L3, fórmula viral:** palavra-chave no início do título, até 60 caracteres e sem jargão. Até 4 palavras na thumb, alto contraste e um único foco visual. Reaproveite a estrutura do outlier, mas troque o ângulo. Nunca copie título ou thumb.
- **L4, roteiro:**
  - Gancho de 0–20 s que já entrega parte da promessa do título.
  - Um micro-ganho a cada 30–60 s, open loops e um pattern interrupt a cada ~90 s.
  - CTA no meio do vídeo. O final aponta para o próximo vídeo da série.
  - A estrutura varia entre vídeos: alterne entre 4 esqueletos, para não parecer "template em massa".
  - Gere 3 aberturas alternativas, para os testes de gancho que o YouTube anunciou.
- **L5, revisão:**
  - Toda afirmação factual precisa de uma fonte do `research.md`. Sem fonte, ela vira [REVISAR].
  - Tire clichês de IA e repetições, e varie o ritmo das frases.
  - Bloqueie promessas de saúde ou dinheiro, título que não é entregue, termo técnico no título, falta de divulgação e imagem com marca ou rosto real.
  - Marque [REVISAR] onde a pessoa deve pôr a opinião dela.
- **D5, edição:**
  - Cenas de 2–8 s conforme a emoção e o texto, Ken Burns em direção alternada e cortes no ritmo da fala.
  - Trilha da Audio Library com ducking, -14 LUFS e capítulos.
  - Os Shorts saem dos MESMOS assets, sem nova chamada de LLM além de reescrever o gancho.
- **D7, QA:**
  - Sem silêncio maior que 1,5 s e sem frame preto. Legenda em sincronia.
  - Título entregue nos primeiros 60 s (checado pela transcrição). Thumb de até 2 MB.
  - Legibilidade da thumb em 168 px. Capítulos começando em 00:00.

### B3. Paralelismo e comunicação

- **Execução:** `asyncio` no Python, com um semáforo de 4 tarefas simultâneas para a API e outro de 2 para FFmpeg.
  - **Onda 1:** L2 ∥ D1 ∥ D2.
  - **Onda 2:** D3 ∥ D4 ∥ D7-thumbs, cena a cena.
- **Produção em bloco:** uma vez por semana, a rodada gera os roteiros de todos os vídeos de uma vez via Batch API (−50%), com o mesmo prefixo cacheado. Depois vêm as vozes e por fim as edições.
- **Barramento:** SQLite (`bus.db`), com a tabela `messages(id, run_id, from_agent, to_agent, type, payload_json, status, created_at)`.
  - Os tipos são `task | result | question | blocker | cost_alert | review_comment`.
  - Os contratos ficam em `schemas/*.py` (pydantic), e a validação é feita com structured outputs (`output_config.format`). Isso evita refazer chamadas por causa de JSON quebrado.
- **Handoff mínimo:** cada agente recebe só os arquivos de que precisa e devolve um resumo de até 150 palavras mais os caminhos dos artefatos. Nunca recebe o histórico inteiro.
- **Perguntas entre agentes:** `question` vai para o agente dono do dado. Sem resposta em 1 ciclo, o orquestrador decide ou leva para a pessoa (label `blocked`).

### B4. Loop e agenda

| O quê | Onde roda | Custo parado |
|---|---|---|
| Ciclo de produção, 2x por dia: lê o calendário (Sheets), mantém um estoque de ≥7 vídeos agendados e avança os runs pendentes | GitHub Actions cron → `python -m darkstudio tick` | zero |
| Lote semanal (roteiros, posts, traduções) | Actions cron, domingo → Batch API | zero |
| Analytics em 48 h, 7 d e 28 d → `learnings.yaml` → PR "playbook: semana N" | Actions cron | zero |
| Supervisão (ler logs, destravar `blocked`, revisar PRs) | `/loop` no Claude Code, ritmo próprio, ≥30 min | só quando ativo |

- **Kill switch:** um arquivo `STOP` ou o custo do dia acima do teto pausa tudo. O bloqueio é feito pelo código e por um hook do Claude Code (skill `update-config`).
- **Retentativa:** a etapa que falhou tenta de novo 3 vezes (2 s, 4 s, 8 s). Depois disso o estado vira `failed(<etapa>)` e o sistema abre uma issue.
- **Qualidade:** QA reprovado devolve o vídeo só para a etapa culpada, no máximo 2 vezes. Na terceira, escala para a pessoa.

### B5. Automação de navegador

- **Playwright, sem LLM:** faz as tarefas de leitura pública abaixo, com no máximo 1 requisição a cada 3 s e respeito ao robots.txt:
  - autocomplete e "pesquisas relacionadas";
  - página pública de canais de referência quando a cota da API acaba;
  - mural de thumbs concorrentes (uso interno);
  - teste de legibilidade da thumb numa grade HTML local que imita os resultados de busca.
- **Claude in Chrome, no navegador da pessoa e com confirmação a cada ação:** fica só para o que a API não cobre:
  - postar na aba Comunidade;
  - configurar "Testar e comparar", que testa até 3 títulos e thumbs;
  - telas finais.
- **Proibido:** login automatizado, criação de contas, aquecimento por robô, interação falsa e rotação de IP ou fingerprint.

### B6. Controle de PR

> **Implementado na v3.1:** a máquina de estados fica em `core/workflow.py`, o diagrama em `docs/WORKFLOW.md` (gerado), a publicação em `docs/AUTOMACAO_PUBLICACAO.md` e a segurança em `docs/SEGURANCA_CREDENCIAIS.md`.

- **Fase de calibração (10 primeiros vídeos):** 1 PR por vídeo, com a branch `video/<canal>/<data>-<slug>`.
- **Depois disso:** 1 PR por lote semanal, com um checklist por vídeo. Assim a pessoa revisa menos vezes e o CI roda menos.
- **Conteúdo do PR:**
  - brief, research, script.final, review.json, qa.json, metadata.yaml, thumbs, cost.json;
  - link do vídeo no Drive (mídia não entra no git);
  - template em `.github/pull_request_template.md`: Resumo | Ângulo | Fontes | Itens [REVISAR] | Compliance | QA | Custo.
- **CI (barato, só valida JSON):** ruff, pytest com mocks, validação de schemas, `review.json` e `qa.json` em `pass`, `cost.json` dentro do teto e varredura de segredos.
- **Publicação:** um workflow `on: push main` (paths `runs/**`) dispara o D8 para os vídeos aprovados.
- **Labels:** `needs-human-review`, `script-approved`, `ready-to-publish`, `blocked`, `cost-alert`.

### B7. Logs e custo

- **Formato:** `logs/<data>.jsonl`, com os campos `{ts, run_id, agent, step, status, model_tier, input_tokens, cached_tokens, output_tokens, cost_usd, duration_ms, artifact, error, request_id}`.
- **Logger:** um único, em `utils/log.py`. Sem `print()` no core.
- **Antes de chamadas grandes:** `count_tokens` para estimar o custo. Ele aborta a chamada se ela fosse estourar o teto do run.
- **Cache:** confira `cache_read_input_tokens`. Se der 0 em chamadas repetidas, há algo invalidando o prefixo (data, uuid ou JSON não ordenado).
- **Dashboard:** uma aba "Custos & Status" no `streamlit_app.py`, que lê o JSONL e o `state.json`.

### B8. Dicas → implementação (20 originais + 30 novas)

**Originais:**

| # | Dica | Onde |
|---|---|---|
| 1 | Nicho: demanda × capacidade | L1 pergunta a capacidade; D1/D2 medem a demanda e a saturação (densidade de outliers) |
| 2 | Micronicho | Campo obrigatório no brief; playbook por micronicho |
| 3 | Contra conteúdo inautêntico | R2, L5, 4 esqueletos de roteiro, revisão humana |
| 4 | Título e thumb | L3 com 10 títulos e 3 thumbs; D7 testa a legibilidade |
| 5 | Outliers | D1 (≥3x a mediana do canal) |
| 6 | Fórmula viral sem jargão | L3 + bloqueio no L5 |
| 7 | Ganchos e micro-ganhos | L4 + checagem de "título entregue" no D7 |
| 8 | Mudar o ângulo | Campo obrigatório `angle.md` (diferença em relação ao outlier) |
| 9 | IA auxiliar | [REVISAR] + aprovação no PR |
| 10 | Voz neural | D3 com persona por canal (velocidade, pausas, ênfase) |
| 11 | Ritmo variado | D5 |
| 12 | Legendas | D6 |
| 13 | A/B de thumbs | D7 gera 3; a pessoa ativa "Testar e comparar" (títulos e thumbs) |
| 14 | Produção em bloco | Lote semanal via Batch API (B3/B4) |
| 15 | Receita além do AdSense | Campo do brief; CTA no L4; divulgação checada pelo L5 |
| 16 | Outros idiomas | Começa com a dublagem automática do YouTube (grátis); abre um canal separado só para o idioma que mostrar tração no analytics |
| 17 | SEO | L3 + D2 |
| 18 | MVP | `--mvp`: 1 Short ponta a ponta por ~US$ 0,01 para validar o nicho |
| 19 | Comunidade | L7 + postagem assistida |
| 20 | Contas "aquecidas" | **Reinterpretada:** checklist manual para a pessoa (canal completo, telefone verificado, uso real) e cadência gradual de 2, depois 3 vídeos por semana, depois o ritmo-alvo. Não achei evidência de que aquecimento por robô ajude, e simular humano viola os termos |

**Novas, vindas da pesquisa** (fontes em `docs/PESQUISA_CANAIS_DARK_2026.md`):

| # | Dica |
|---|---|
| 21 | Marque `containsSyntheticMedia` pela API (campo oficial desde 10/2024). |
| 22 | Nunca dê a entender que o conteúdo é oficial. Screen Culture e KH Studio, de trailers falsos de IA, perderam a monetização, recuperaram ao rotular "fan-made" e foram **encerrados** depois de parar de rotular. |
| 23 | Produção em massa por template derruba canais grandes. 16 canais com 35 mi de inscritos foram removidos, inclusive de quiz religioso. Nicho gospel/espiritualidade não é imune. |
| 24 | Título que promete e não entrega é penalizado pelos sinais de satisfação. Checagem automática no QA. |
| 25 | Os primeiros 30 s são o ponto crítico: meça a retenção aos 30 s e itere o gancho. |
| 26 | Prepare 3 aberturas por vídeo para os testes de gancho e de cortes de Short anunciados pelo YouTube. |
| 27 | Mostre as fontes na tela e na descrição, como faz o Kurzgesagt. Isso aumenta a confiança e reduz o risco. |
| 28 | Política de correção: comentário fixado com a errata; se o erro for grave, despublique. |
| 29 | Deep dives de 30–60 min em história e documentário (evergreen). Teste ao lado do formato de 8–15 min. |
| 30 | Shorts derivados do longo com link de "vídeo relacionado": funil a custo quase zero. |
| 31 | Séries com formato fixo e playlists, para aumentar o tempo de sessão. |
| 32 | Telas finais e cards apontando para o próximo vídeo da série. |
| 33 | Capítulos automáticos a partir das cenas. |
| 34 | Comentário fixado com pergunta e CTA; responder às pessoas nas 2 primeiras horas é tarefa humana. |
| 35 | Horário de publicação pelo "quando seu público está on-line", não por achismo. |
| 36 | Leia o gráfico de retenção: quedas maiores que 10% viram aprendizado para o roteirista. |
| 37 | Matar ou escalar: depois de 10 vídeos, CTR abaixo de 3% e AVD abaixo de 30% indicam pivotar o micronicho; acima da meta, dobrar a frequência. |
| 38 | Mix de 70% evergreen e 30% tendência. |
| 39 | Biblioteca de ganchos que funcionaram (`hooks.yaml`), reaproveitados com ângulo novo. |
| 40 | Brand kit por canal: fontes, cores, estilo de thumb e voz. Identidade visual própria é o "fosso" dos grandes canais sem rosto. |
| 41 | Licenças: música da Audio Library ou CC0; imagens geradas ou de Pexels/Pixabay; registro em `licenses.json`. Evite Edge-TTS em canal monetizado (uso comercial fora do Edge é zona cinzenta). |
| 42 | Banco de assets reaproveitável por palavra-chave: corta o custo de imagem entre vídeos do mesmo nicho. |
| 43 | Receita própria: os grandes canais sem rosto vivem muito de loja e apoio do público (o Kurzgesagt tira a maior parte da receita de produtos e doações). |
| 44 | Lista de palavras de risco de desmonetização por nicho, checada pelo L5. |
| 45 | Requisitos do YPP mudam por país: confira os atuais no Studio antes de planejar a meta. |
| 46 | Qualidade acima de quantidade: o teto semanal vem da capacidade de revisão humana declarada no Grill. |
| 47 | Backup no Drive (`storage/drive.py`); mídia local fica só 30 dias. |
| 48 | Reavalie a cada trimestre os nichos e o "estoque" de outliers. Nicho saturado vira micronicho ou é abandonado. |
| 49 | Tenha um "canal-laboratório" no modo `--mvp` para testar nichos sem arriscar o canal principal, sempre com conteúdo legítimo e não duplicado. |
| 50 | Um roteiro humanizado e verificado vale mais que 10 genéricos. Os canais encerrados tinham escala; os que sobrevivem têm identidade. |

### B9. Skills: reavaliação de custo-benefício

**Critério:** quanto custa em tokens por uso, quantas vezes é usada e o que evita de retrabalho ou risco.

| Pos. | Skill | Uso no projeto | Custo | Veredito |
|---|---|---|---|---|
| 1 | `claude-api` | Preços, cache, Batch, structured outputs, count_tokens | Leitura única | **Essencial**, é a base da economia |
| 2 | `session-start-hook` | Instala ffmpeg e as dependências nas sessões na nuvem | Só para configurar | **Essencial** |
| 3 | `update-config` (hooks) | Kill switch `STOP`, bloqueio de push na main, teto de custo | Só para configurar; hooks rodam sem token | **Nova e essencial** |
| 4 | `run` | Rodar o pipeline e o Streamlit para ver o resultado | Baixo | Manter |
| 5 | `code-review` | PRs de código, **no nível low/medium** (o max lança muitos subagentes) | Médio | Manter, com limite |
| 6 | `security-review` | Só nos PRs que mexem em credenciais, OAuth ou CI | Médio, raro | Manter |
| 7 | `fewer-permission-prompts` | Menos interrupções na supervisão | Uso único | **Nova** |
| 8 | `skill-creator` | Criar `grill-me`, `yt-compliance` e `outlier-hunter` | Médio; evals custam | Manter, com evals só no grill e no compliance |
| 9 | `loop` | Só supervisão; o agendamento foi para o Actions | Cada tick é uma chamada | **Rebaixada** |
| 10 | `google-workspace` | Calendário editorial e custos no Sheets | Baixo | Substitui o `xlsx` |
| sit. | `deep-research` | **1 vez por nicho novo** | Alto (lança subagentes) | Situacional, era 4º |
| sit. | `chrome-browser` | Só as ações assistidas da B5 | Médio (screenshots) | Situacional; o Playwright faz o resto de graça |
| — | `xlsx` | O projeto não gera .xlsx | — | **Removida** |
| — | `simplify`, `dataviz` | Limpeza pontual; gráficos do dashboard | Baixo | Opcionais |

**Skills próprias** (em `.claude/skills/`, criadas com o `skill-creator`): `grill-me`, `yt-compliance`, `outlier-hunter`, `hook-script`. As outras viram prompts do pipeline, e não skills, porque rodam fora do Claude Code.

### B10. Roadmap (1 PR por fase)

| Fase | Entrega |
|---|---|
| **F1** | `utils/log.py`, `schemas/`, máquina de estados, cache por hash, `bus.db`, pytest com mocks, hooks de STOP e custo |
| **F2** | Cliente LLM com tiers e fallback, Grill, perfil de canal, `--mvp` (1 Short ponta a ponta) |
| **F3** | D1 Outliers, D2 Autocomplete, L2 Pesquisador, L3 Estrategista |
| **F4** | L4 Roteirista, L5 Revisor, Batch semanal |
| **F5** | D3 Kokoro, D4 banco de assets, D5 FFmpeg em um passo com Shorts derivados, D6, D7 |
| **F6** | PR por vídeo e por lote, CI, D8 com `containsSyntheticMedia` |
| **F7** | L6 Analista, `learnings.yaml`, dashboard de custo |
| **F8** | Dublagem e idiomas, L7 Comunidade, ações assistidas no navegador |

**Antes da F1, faça o Grill da implementação:**
- quais canais e nichos;
- quais chaves de API já existem;
- se há GPU local;
- qual o teto mensal;
- ~~se mantém o OpenAI~~ **decidido na v3:** Claude no roteiro e Gemini como alternativa. OpenAI e Groq foram removidos.

### B11. Ponderação: dicas, observações e arquitetura

Cada item recebe quatro notas, que definem a ordem de implementação e o peso nas decisões do orquestrador:
- **Impacto** (1–5)
- **Esforço/custo** (1–5; 1 é barato)
- **Risco se ignorado** (1–5)
- **Evidência:** F (forte: política oficial ou caso documentado), M (média: consenso entre fontes) ou f (fraca: afirmação de fornecedor ou anedota)

**Prioridade** = Impacto + Risco − Esforço, com ajuste pela evidência: F +1, f −1.

**Dicas**

| Prioridade | Dicas | I | E | R | Ev | Por quê |
|---|---|---|---|---|---|---|
| **P0 (fazer primeiro)** | 3 contra conteúdo inautêntico, 21 `containsSyntheticMedia`, 22 não parecer oficial, 23 sem template em massa | 5 | 2 | 5 | F | É o que encerrou canais com milhões de inscritos. Sem isso, o resto não importa |
| P0 | 4 título e thumb, 13 A/B nativo | 5 | 2 | 3 | F | Recurso oficial do Studio; o CTR abre a distribuição |
| P0 | 7 gancho, 24 título entregue, 25 retenção aos 30 s | 5 | 2 | 4 | M | Consenso entre as fontes; checagem barata no QA |
| P0 | 9 IA como auxiliar, 46 qualidade > quantidade | 5 | 3 | 5 | F | É a revisão humana que separa os sobreviventes dos encerrados |
| P1 | 2 micronicho, 5 outliers, 8 mudar o ângulo, 1 nicho | 4 | 2 | 3 | M | Script barato (D1), alto retorno na escolha de tema |
| P1 | 14 produção em bloco, 30 Shorts derivados, 42 banco de assets | 4 | 2 | 2 | M | Reduzem custo e tempo diretamente |
| P1 | 17 SEO, 33 capítulos, 31/32 séries e telas finais | 3 | 1 | 2 | M | Quase grátis, ganho acumulado |
| P1 | 27 fontes na tela, 28 política de correção | 3 | 1 | 3 | F | Prática do Kurzgesagt; reduz risco de desinformação |
| P1 | 10 voz neural, 41 licenças | 4 | 2 | 4 | M | Voz ruim derruba retenção; licença errada derruba canal |
| P2 | 12 legendas (o "+20–30%" é f), 11 ritmo variado | 3 | 2 | 2 | M/f | Úteis, mas o ganho numérico citado não tem fonte primária |
| P2 | 15/43 receita própria e afiliados | 4 | 3 | 1 | M | Importante depois da tração, não antes |
| P2 | 16 idiomas (via dublagem automática primeiro) | 4 | 2 | 1 | M | Teste grátis antes de abrir canal novo |
| P2 | 19 Comunidade, 34 comentário fixado, 35 horário | 2 | 1 | 1 | M | Ganho marginal, custo baixo |
| P2 | 29 deep dives de 30–60 min, 26 três aberturas | 3 | 3 | 1 | f | Testar no modo laboratório antes de padronizar |
| P3 | 18 MVP, 49 canal-laboratório | 3 | 1 | 1 | M | Ferramenta de validação, não de crescimento |
| **Descartada como escrita** | 20 aquecer conta simulando humano | 0 | — | 5 | f/negativa | Sem evidência de ganho e viola os termos. Fica só o checklist manual e a cadência gradual |

**Observações da pesquisa**

| Observação | Peso | Efeito no sistema |
|---|---|---|
| Os sobreviventes têm equipe, pesquisa e identidade própria | Alto (F) | O L5 e a aprovação humana são obrigatórios; o brand kit (40) sobe para P1 |
| Rotular salvou e não rotular encerrou (Screen Culture) | Alto (F) | R4 vira bloqueio no CI, não aviso |
| Nicho religioso ou de quiz não protege de produção em massa | Alto (F) | O L5 checa a similaridade entre os últimos 10 roteiros do canal; similaridade acima de 0,8 bloqueia |
| "Satisfação é o sinal principal desde abr/2026" | Baixo (f) | Não muda a arquitetura; usa retenção aos 30 s e "título entregue", que são mensuráveis |
| Números de inscritos de blogs divergem | Médio | O D1 usa a API oficial, nunca números de blog |
| Edge-TTS em uso comercial é zona cinzenta | Médio (M) | Kokoro como padrão |

**Decisões de arquitetura**

| Decisão | Alternativa | Escolha | Motivo |
|---|---|---|---|
| Pipeline Python com a API do Claude | Subagentes do Claude Code | **Pipeline** | Ordens de grandeza mais barato e reprodutível; o Claude Code fica para dev e supervisão |
| 7 agentes com LLM + 8 scripts | 19 agentes com LLM | **7+8** | Menos chamadas e menos handoff; revisão numa chamada estruturada |
| Cron do GitHub Actions | `/loop` ou cron local | **Actions** para orquestrar; **render local** quando houver GPU ou muitos vídeos | O Actions é grátis parado, mas o render consome minutos (2000/mês em repo privado) |
| PR por vídeo e depois por lote | Sempre por vídeo | **Híbrido** | Calibra nos 10 primeiros, depois economiza tempo de revisão |
| Barramento SQLite | Arquivos JSON soltos ou fila externa | **SQLite** | Zero infraestrutura, transacional, fácil de inspecionar |
| Kokoro local | ElevenLabs | **Kokoro**; ElevenLabs só no canal que já monetiza | Custo zero; trocar quando a receita pagar |
| Banco de assets + geração local | API de imagem por cena | **Banco + local** | Reaproveita entre vídeos; API só como último recurso |
| Dublagem automática do YouTube | Canal por idioma desde o início | **Dublagem primeiro** | Mede a demanda por idioma sem custo; abre canal só onde houver tração |
| Haiku por padrão | Sonnet em tudo | **Haiku**; Sonnet só em L3/L4 | Haiku custa cerca de 1/20 do Sonnet; escala só se a validação falhar |

**Regra para o orquestrador:** com tempo ou orçamento limitado, implemente e mantenha primeiro os itens P0. Um item P2 nunca atrasa um P0. Reavalie as notas a cada trimestre com o `learnings.yaml`: uma evidência própria do canal (F) vale mais que qualquer fonte externa.

### B12. Fontes externas do usuário (NotebookLM)

As 20 dicas originais citam fontes numeradas [1–69], provavelmente do caderno NotebookLM do usuário. Quando o conteúdo desse caderno estiver acessível, por exportação para o Google Docs/Drive ou colado no chat:
1. Extraia as dicas novas.
2. Classifique cada uma com as notas da B11.
3. Descarte as que violem R2–R4.
4. Acrescente as demais à B8 com a citação da fonte.

Não invente conteúdo do caderno.

### B13. Plataforma: Antigravity como IDE e Claude Code como harness

| Camada | Ferramenta | Papel |
|---|---|---|
| IDE/plataforma | Google Antigravity | Editor, terminal integrado, preview do Streamlit, gerenciador de agentes |
| **Harness** (escreve código e orquestra) | **Claude Code**, pela extensão no Antigravity ou pela CLI `claude` no terminal integrado | Único agente que escreve no repositório. Lê `CLAUDE.md`, `.claude/settings.json` (hooks), `.claude/skills/` e `.mcp.json` |
| Segundo modelo | Gemini via `agy` (Antigravity CLI), em modo não interativo | Só leitura: revisão cruzada de roteiro e PR, pesquisa com Google Search, análise multimodal de thumbs e vídeos concorrentes |
| Runtime de produção | Pipeline Python: Claude (`anthropic`) como principal e Gemini (`google-genai`) para alternativa, transcrição e TTS | Não depende de IDE: roda igual no Actions, no terminal ou no Antigravity |

**Regras:**
- **Um escritor só:** o agente nativo do Antigravity não edita o repositório ao mesmo tempo que o Claude Code. Se a pessoa quiser usá-lo, que seja numa branch ou worktree separada.
- **Comunicação Claude Code → agy, por arquivo:**
  1. O Claude Code escreve `runs/<id>/agy/task.md` (tarefa, arquivos de entrada e formato da resposta).
  2. Chama o `agy` sem interação e com política de aprovação **somente leitura**.
  3. Lê `runs/<id>/agy/result.md`, valida e registra no JSONL com `agent="agy"`.
  - Use timeout e limite o tamanho da saída.
- **Quando chamar o agy:** só em itens P0/P1 da B11. Por exemplo, a revisão cruzada do roteiro antes do OK humano, porque um modelo diferente pega erros diferentes, ou a checagem de fatos com fonte. Nunca dentro do laço por cena.
- **Flags do agy:** confirme com `agy --help`. O modo não interativo e a política de aprovação mudaram em relação ao antigo Gemini CLI, então não copie flags de tutoriais antigos.
- **Skills:**
  - O Claude Code lê `.claude/skills/`; o Antigravity usa `.agents/skills/`.
  - A fonte única fica em `.claude/skills/`. Se o formato `SKILL.md` for compatível na versão instalada, crie o link `.agents/skills -> ../.claude/skills`.
- **Regras compartilhadas:** `CLAUDE.md` vale para o Claude Code. O `AGENTS.md` aponta para ele, para que qualquer agente siga as regras R1–R7.
- **Hooks:** STOP, teto de custo e bloqueio de push na main ficam em `.claude/settings.json`. São do harness, então valem em qualquer IDE.
- **Navegador:** a automação de leitura continua no Playwright, e as ações assistidas da B5 continuam com confirmação da pessoa. O navegador do Antigravity é controlado pelo agente do Antigravity, que não é o harness, então ele não faz ações em nome do sistema.
- **Passo a passo de instalação:** `docs/ANTIGRAVITY.md`.

---

## Estimativa de custo por vídeo longo (v2)

São estimativas de projeto, ainda não medidas. Recalibre com o `cost.json` dos 10 primeiros vídeos.

| Etapa | Tier | Tokens (entrada/saída, aprox.) | US$ |
|---|---|---|---|
| Grill (1–3 rodadas) | Haiku | 5k / 1k | ~0,001 |
| Pesquisa | Haiku | 30k / 2k | ~0,004 + taxa de busca |
| Estratégia+SEO | Sonnet, com cache | 8k / 1,5k | ~0,02 |
| Roteiro | Sonnet, com cache | 12k / 4k | ~0,045 |
| Revisão | Haiku | 15k / 4k | ~0,004 |
| Analytics + posts | Haiku Batch | — | <0,002 |
| **Subtotal LLM** | | | **~0,08** |
| Voz (Kokoro), edição, legendas, thumbs | local | — | 0 |
| Imagens | banco de assets + local; API só se faltar | — | 0–0,10 |
| **Total** | | | **~0,08–0,18** |

- **Na Batch API:** os roteiros do lote semanal custam cerca de metade.
- **Shorts derivados:** cerca de US$ 0,005 cada.
- **Comparação:** rodar o mesmo trabalho como subagentes do Claude Code custaria ordens de grandeza a mais, porque cada subagente começa do zero e relê o contexto. Por isso a v2 separa a supervisão (Claude Code) da execução (pipeline).

## Changelog v3 → v3.1

- **Workflow:** máquina de estados com portões humanos, `events.jsonl` por vídeo e doc gerada que o CI valida.
- **Publicação:** GitHub Actions com o ambiente protegido `youtube-production`. O vídeo sobe privado com `publishAt` e `containsSyntheticMedia`. O Drive é lido via OIDC/WIF, sem chave.
- **Segurança:**
  - `.gitignore` ampliado;
  - `scripts/check_secrets.py` no CI e no pre-commit;
  - logs mascarados;
  - `.claude/settings.json` impede o agente de ler credenciais, publicar, fazer merge ou mexer em secrets;
  - hook STOP testado.

## Changelog v2 → v3

- **Código:**
  - Saíram `services/openai_service.py` e `services/groq.py`.
  - Entraram `services/claude_service.py` (saída estruturada, cache no system e tratamento de recusa) e `services/script_router.py` (Claude → Gemini).
  - `services/gemini.py` migrou para o `google-genai`: roteiro em JSON, transcrição com timestamps e TTS em WAV.
  - `VoiceService` usa Kokoro → Gemini TTS.
  - Novos testes em `tests/` (pytest com dublês, sem rede).
- **Plataforma:** Antigravity + harness Claude Code + `agy` como segundo modelo (B13, `docs/ANTIGRAVITY.md`, `CLAUDE.md`, `AGENTS.md`).

## Changelog v1 → v2

- **Execução:** sai dos subagentes do Claude Code e vai para um pipeline Python com a API do Claude.
- **Agentes:** 19 viraram 7 com LLM e 8 determinísticos. Os revisores (fatos, humanização e compliance) viraram uma chamada estruturada.
- **Agenda:** do `/loop` para o cron do GitHub Actions. O `/loop` ficou só para supervisão.
- **Voz:** de Edge-TTS para Kokoro (Apache 2.0), com cota grátis oficial de TTS na nuvem como plano B.
- **Novidades:** structured outputs, `count_tokens`, PR por lote depois da calibração, Shorts derivados sem LLM, banco de assets, `containsSyntheticMedia` e 3 aberturas por vídeo.
- **Skills:** `update-config` e `fewer-permission-prompts` entraram. `xlsx` saiu. `deep-research` e `chrome-browser` ficaram situacionais. `loop` foi rebaixada.
- **Estrutura:** núcleo compacto para o `CLAUDE.md` e anexos sob demanda (menos tokens por mensagem).
- **Dicas:** 30 novas (21–50) a partir da pesquisa de canais e políticas de 2025–2026.
