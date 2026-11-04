# Antigravity como IDE, Claude Code como harness

O Google Antigravity é a plataforma de trabalho: editor, terminal e preview. Quem escreve código e orquestra o sistema é o **Claude Code**. O Gemini entra de duas formas:
- no **pipeline**, pela API (`google-genai`): roteiro alternativo, transcrição e TTS;
- na **IDE**, pela CLI `agy`: segundo modelo, só leitura.

> **Aviso sobre a precisão:** a documentação oficial da Anthropic não cita o Antigravity pelo nome. O passo da extensão vem da instrução geral para forks do VS Code. Os detalhes do `agy` vêm de guias de terceiros. Confira cada comando no site oficial antes de executar.

## 1. Instalação

1. **Antigravity:** instale pelo site oficial e abra a pasta do repositório.
2. **Claude Code (harness):**
   - No painel de extensões do Antigravity, busque **"Claude Code"** do publicador **Anthropic** no Open VSX. Não instale extensões com nome parecido de outros publicadores.
   - Se a instalação falhar (há relato de erro em loop quando o comando `code` não está no PATH), use a CLI no terminal integrado:
     ```bash
     curl -fsSL https://claude.ai/install.sh | bash
     claude          # na primeira execução: /login (assinatura) ou ANTHROPIC_API_KEY
     ```
   - A extensão traz a própria cópia do Claude Code para o painel de chat, mas não instala o comando `claude` no terminal. Para usar os dois, instale também a CLI.
3. **Antigravity CLI (`agy`)**, para o Gemini como segundo modelo:
   ```bash
   curl -fsSL https://antigravity.google/cli/install.sh | bash   # confira a URL no site oficial
   agy --help                                                    # confira as flags do modo não interativo
   ```
   - Se o binário não for encontrado, adicione `~/.local/bin` ao PATH.
   - Se ele conflitar com o binário do app desktop, ajuste o link simbólico conforme o guia oficial.
4. **Python:**
   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements-dev.txt
   pip install -r requirements-local-tts.txt   # opcional: voz Kokoro local, grátis
   cp .env.example .env                        # preencha ANTHROPIC_API_KEY e GEMINI_API_KEY
   python -m pytest                            # sem rede
   streamlit run streamlit_app.py              # abra o preview no Antigravity
   ```

## 2. Quem faz o quê

| Tarefa | Quem | Como |
|---|---|---|
| Escrever ou alterar código, abrir PR | Claude Code | Branch `feat/*`, testes, `/code-review low` |
| Orquestrar e supervisionar o pipeline | Claude Code | `/loop` com ritmo próprio, só quando ativo |
| Produzir vídeos | Pipeline Python | Claude (roteiro) → Gemini (alternativa), Gemini (transcrição e TTS) |
| Revisão cruzada de roteiro ou PR | Gemini via `agy` | Só leitura; responde em `runs/<id>/agy/result.md` |
| Pesquisa com Google Search, análise de thumbs e vídeos | Gemini via `agy` ou pipeline | Só leitura |
| Agenda | GitHub Actions cron | Zero token parado |

## 3. Comunicação Claude Code ↔ agy

1. O Claude Code cria `runs/<id>/agy/task.md` com o objetivo, os arquivos de entrada, o formato da resposta (JSON ou Markdown) e o limite de tamanho.
2. Chama o `agy` sem interação, com política de aprovação **somente leitura** e timeout. As flags exatas saem do `agy --help`.
3. O `agy` escreve `runs/<id>/agy/result.md`. O Claude Code valida o resultado, registra no `logs/<data>.jsonl` com `agent="agy"` e decide o que aproveitar.
4. O `agy` nunca faz commit nem push e nunca edita fora de `runs/<id>/agy/`.

## 4. Arquivos de configuração

| Arquivo | Lido por | Conteúdo |
|---|---|---|
| `CLAUDE.md` | Claude Code | Regras R1–R7 e o fluxo |
| `AGENTS.md` | Outros agentes | Aponta para o `CLAUDE.md`; diz que só o Claude Code escreve |
| `.claude/settings.json` | Claude Code | Hooks (STOP, teto de custo, bloqueio de push na main) e permissões |
| `.claude/skills/` | Claude Code | Skills próprias (`grill-me`, `yt-compliance`, ...) |
| `.agents/skills/` | Antigravity | Opcional: link para `.claude/skills/` se o formato for compatível |
| `.env` | Pipeline | Chaves e modelos (veja `.env.example`) |

## 5. Custos

- **Claude Code:** usa a assinatura Claude ou a chave da API. O pipeline usa a chave da API.
- **Pipeline:** o tier do roteiro é configurável (`CLAUDE_MODEL_SCRIPT`, `CLAUDE_EFFORT_SCRIPT`). O padrão é o tier Sonnet com esforço medium. Para gastar menos, use o tier Haiku; para mais qualidade, o tier Opus.
- **Gemini:** a cota grátis do AI Studio cobre a alternativa de roteiro, a transcrição e os testes de TTS. Os IDs mudam com frequência: rode `python list_models.py`.
- **agy:** só em itens P0/P1 (anexo B11 do prompt). Nunca dentro do laço por cena.

## Fontes

- [Claude Code para VS Code e forks](https://code.claude.com/docs/en/vs-code)
- [Relato de falha da extensão no Antigravity](https://claudeissues.com/issue/22360-bug-cli-fails-to-start-in-google-antigravity-error-installing-vs-code-extension)
- [Guia do Antigravity CLI (agy)](https://pasqualepillitteri.it/en/news/3422/antigravity-cli-agy-install-migrate-gemini-cli)
- [Codelab do Antigravity CLI](https://codelabs.developers.google.com/antigravity-cli-hands-on?hl=vi)
- [Modelos do Gemini](https://ai.google.dev/gemini-api/docs/models/gemini?authuser=00&hl=tr)
