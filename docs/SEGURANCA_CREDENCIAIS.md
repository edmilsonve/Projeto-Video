# Segurança das credenciais

## 1. Verificação feita em 04/11/2026

| Item | Resultado |
|---|---|
| Visibilidade do repositório | **Público.** Tudo que for commitado fica visível para qualquer pessoa. |
| Histórico do git (6 commits, todas as branches) | Varredura por regex de chaves Anthropic, Google, OAuth, GitHub, Replicate, chaves privadas e JSON de conta de serviço: **nada encontrado** |
| Arquivos de credencial versionados | **Nenhum** (`.env`, `service_account.json`, `client_secret*.json`, tokens) |
| Código | Todas as chaves vêm de variáveis de ambiente; nenhuma está escrita no código |
| Varredura do GitHub (Advanced Security) | Indisponível pela API neste repositório. Ative *Secret scanning* e *Push protection* em Settings (grátis para repositório público) |
| Falhas encontradas e corrigidas | `client_secret.json` e arquivos de token **não estavam** no `.gitignore` (o `.env.example` aponta para `client_secret.json`). Corrigido, e o CI agora bloqueia esses arquivos |

## 2. Inventário

| Credencial | Para quê | Onde fica | Escopo mínimo | Se vazar | Rotação/revogação |
|---|---|---|---|---|---|
| `ANTHROPIC_API_KEY` | Roteiro (pipeline local) | `.env` local (ignorado) | Workspace próprio com **limite de gasto** | Uso da sua conta até o limite | Console da Anthropic; trocar a cada 90 dias |
| `GEMINI_API_KEY` | Alternativa de roteiro, transcrição, TTS | `.env` local | Chave **restrita à Generative Language API** no Google Cloud | Uso da cota | Google Cloud / AI Studio |
| `STABILITY_API_KEY` | Imagens | `.env` local | — | Créditos | Painel da Stability |
| **OAuth do YouTube** (client id/secret + refresh token) | Envio de vídeo e thumbnail | Local: `~/.config/darkstudio/youtube.json` (0600, fora do repositório). CI: secrets do ambiente `youtube-production` | **Só `youtube.upload`**: permite enviar, mas não apagar vídeos nem mudar o canal | Alguém pode **enviar vídeos ao seu canal** | myaccount.google.com/permissions (revogar) + `scripts.youtube_auth` |
| Drive no CI | Ler o `.mp4` | **Nenhuma chave guardada**: OIDC → Workload Identity Federation | Conta de serviço leitora de **uma pasta**, só para este repositório na `main` | — | Remover o binding no IAM |
| `GITHUB_TOKEN` | CI e registro do estado | Gerado por job, expira no fim | `contents: read` no CI; `write` só no job de publicação | Escrita no repositório durante o job | Automático |
| Login do Claude Code / Antigravity | Harness / IDE | Perfil local do usuário | — | Uso da assinatura | Logout / revogar sessão |

## 3. Controles implementados

1. **Nada de segredo no repositório:**
   - `.gitignore` ampliado;
   - `scripts/check_secrets.py` roda no CI e como pre-commit (`sh scripts/install_git_hooks.sh`). Ele nunca imprime o valor encontrado.
2. **O agente não toca em credenciais nem publica** (`.claude/settings.json`):
   - não pode ler `.env`, `client_secret*`, tokens nem `~/.config/darkstudio`;
   - não pode rodar `scripts.publish`, `scripts.youtube_auth` nem `gh secret`;
   - não pode fazer merge de PR, force push ou push na `main`.
3. **Kill switch:** um arquivo `STOP` bloqueia Bash e edições do agente, por hook. Testado.
4. **Logs mascarados:** `utils/log.py` troca por `***` qualquer valor com cara de chave ou token.
5. **Publicação com dois portões humanos** e secrets que só existem no ambiente protegido, depois da aprovação.
6. **Drive sem chave no CI** (Workload Identity Federation com condição de repositório e branch).
7. **Workflows endurecidos:**
   - permissões mínimas;
   - `persist-credentials: false` no CI;
   - o input manual chega por variável de ambiente, nunca interpolado no shell, e o `run_id` é validado contra path traversal;
   - `concurrency` evita duas publicações simultâneas.
8. **Arquivo local de credenciais** criado com permissão 600. O publicador recusa usá-lo se outros usuários puderem lê-lo.
9. **Vídeo sempre privado + `publishAt`:** um erro de metadados nunca deixa um vídeo público na hora.

## 4. Riscos que continuam (e recomendações)

| Risco | Recomendação |
|---|---|
| Repositório público: briefs e roteiros em `runs/` ficam visíveis **antes** do lançamento | Se isso importar, mova `runs/` para um repositório **privado** de conteúdo. Custo: em plano Free/Pro/Team, o revisor obrigatório de ambiente só existe em repositório público. No privado, o portão passa a ser o merge mais o disparo manual |
| As regras `Read(...)` bloqueiam a ferramenta Read, mas um comando Bash ainda poderia ler um arquivo | Ative o sandbox do Claude Code nas **suas** configurações (`"sandbox": {"enabled": true}` em `~/.claude/settings.json`), que aplica as regras de leitura também ao Bash. Mantenha o arquivo do YouTube fora do repositório |
| Actions de terceiros (`google-github-actions/auth`) referenciadas por tag | Fixe por SHA do commit e ative o Dependabot para actions |
| Gemini no nível gratuito: o Google pode usar entradas e saídas para melhorar produtos, com revisão humana | Use o nível pago (faturamento ativo) se os roteiros forem confidenciais |
| Prompt injection vindo de páginas pesquisadas | Já mitigado: o agente não lê credenciais, não publica e não faz merge. Mantenha assim |
| Limite de 100 refresh tokens por conta e cliente OAuth | Não rode `youtube_auth` repetidamente: cada nova autorização pode invalidar a mais antiga |

## 5. Se uma credencial vazar

1. **Revogue primeiro.** YouTube: myaccount.google.com/permissions. Anthropic, Google e Stability: no painel de cada um.
2. Gere uma nova e atualize o `.env` local ou os secrets do ambiente.
3. Confira os envios recentes no YouTube Studio e os logs de uso de cada provedor.
4. Se o segredo foi commitado, revogar é obrigatório: apagar do histórico não basta, porque o repositório é público.
5. Rode `python scripts/check_secrets.py` e registre o incidente no `CHANGELOG`.
