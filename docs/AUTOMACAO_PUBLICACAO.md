# Automação do processo e publicação no YouTube

## 1. Como o workflow é controlado e documentado

| Necessidade | Solução | Onde |
|---|---|---|
| Uma fonte única da verdade | Máquina de estados declarada em código: estados, transições, dono e artefatos exigidos | `core/workflow.py` |
| A documentação nunca diverge | `docs/WORKFLOW.md` é **gerado** do código; o CI falha se estiver desatualizado | `scripts/gen_workflow_docs.py` |
| Trilha de auditoria por vídeo | `runs/<id>/state.json` (escrita atômica) e `runs/<id>/events.jsonl` (`from`, `to`, `actor`, `note`) | `core/workflow.py` |
| Trilha global e custo | `logs/<data>.jsonl`, com segredos mascarados antes de gravar | `utils/log.py` |
| Portões humanos | `reviewed → script_approved` e `pr_open → approved` só aceitam `actor="human:<nome>"` | `HUMAN_GATES` |
| Revisão do conteúdo | PR por vídeo (calibração), depois por lote semanal | GitHub |
| Aprovação da publicação | Ambiente `youtube-production` com revisor obrigatório; o histórico de deployments mostra quem aprovou e quando | GitHub Environments |
| Parada de emergência | Arquivo `STOP` na raiz: um hook bloqueia Bash e edições do agente | `.claude/settings.json` |

São **dois portões humanos** antes de qualquer vídeo sair:
1. O **merge do PR** aprova o conteúdo.
2. A **aprovação no ambiente protegido** libera a publicação.

O agente não consegue passar por nenhum dos dois: as ferramentas de merge e o comando de publicação estão bloqueados para ele.

## 2. Opções avaliadas para publicar

| Critério | A. Script local | **B. GitHub Actions + ambiente protegido** | C. Make/n8n/Zapier | D. Manual no Studio |
|---|---|---|---|---|
| Onde fica o token do canal | No seu computador, onde o agente também roda | **Secret do ambiente, liberado só após a aprovação, nunca no computador do agente** | Em um terceiro | Nenhum |
| Exposição a prompt injection (o agente lê a web) | Média: o token está na mesma máquina | **Baixa: o agente não tem acesso** | Baixa | Nenhuma |
| Precisa de máquina ligada | Só no envio | **Não** | Não | Sim |
| Auditoria | `events.jsonl` | **`events.jsonl` + deployments + logs do Actions** | Painel do terceiro | Nenhuma |
| Custo | 0 | **0 (repositório público)** | Pago por operação | Tempo humano |
| Escala (lote semanal) | Boa | **Boa** | Boa | Ruim |

**Recomendação: B como caminho principal**, com o vídeo enviado como **privado + `publishAt`**. Quem torna o vídeo público na hora marcada é o próprio YouTube, então o job pode rodar logo após a aprovação, uma vez por semana para o lote inteiro.
- **A** fica como alternativa, rodado por você no seu terminal (`--dry-run` para validar).
- **C** foi descartada: entrega o token de upload do canal a um terceiro e cobra por operação.
- **D** continua valendo para um vídeo fora do lote.

## 3. Fluxo fim a fim

1. O pipeline local produz o vídeo, chega a `qa_passed` e grava `runs/<id>/metadata.json`. O `.mp4` vai para `final_videos/`, numa pasta sincronizada pelo **Google Drive para computador**.
2. O agente abre o PR (`pr_open`). A pessoa revisa os itens [REVISAR], as fontes, o compliance e o custo, e faz o **merge**.
3. O merge na `main` dispara `.github/workflows/publish.yml`. O job **espera a aprovação** no ambiente `youtube-production`.
4. Depois de aprovado, o job:
   - lê o vídeo do Drive (OIDC → Workload Identity Federation, sem chave);
   - marca `approved` com o nome de quem aprovou;
   - envia ao YouTube como privado com `publishAt`, `containsSyntheticMedia` e a thumbnail;
   - grava `youtube.json` e marca `scheduled`;
   - registra o estado de volta na `main`.
5. O YouTube publica no horário marcado. O Analista acompanha 48 h, 7 d e 28 d.

## 4. Configuração única (checklist)

**Google Cloud / YouTube**
1. Crie um projeto e ative a **YouTube Data API v3**.
2. Tela de consentimento OAuth:
   - tipo Externo;
   - **apenas o escopo `youtube.upload`**;
   - status **"Em produção"**. Em "Teste", o refresh token expira em 7 dias. Escopos sensíveis em produção podem exigir verificação do app: confira na documentação do Google.
3. Crie a credencial OAuth do tipo **"App para computador"**. Baixe o JSON para **fora** do repositório.
4. **Peça a auditoria da API** (formulário "YouTube API Services – Audit and Quota Extension"). **Este é o bloqueio mais importante:** projetos não verificados criados depois de 28/07/2020 têm os uploads pela API **travados como privados** até passar na auditoria. Sem ela, nenhum vídeo fica público, nem com `publishAt`.
5. Cota: o padrão é 10.000 unidades por dia. As fontes divergem sobre o custo do `videos.insert` (1.600 unidades no valor histórico; páginas recentes citam 100 ou 1). Confira no Cloud Console. Mesmo com 1.600, cabem cerca de 6 envios por dia, o que basta para o lote semanal.
6. Thumbnail personalizada exige o **canal verificado por telefone**.

**Autorização do canal** (uma vez, no seu computador):
```bash
python -m scripts.youtube_auth --client-secret ~/Downloads/client_secret_xxx.json
# grava ~/.config/darkstudio/youtube.json (permissão 600), fora do repositório
```

**GitHub** (o repositório é público, então tudo abaixo é grátis):
1. *Settings → Environments → New environment* com o nome `youtube-production`:
   - *Required reviewers*: você. Para quem trabalha sozinho, deixe "Prevent self-review" desligado.
   - *Deployment branches*: só `main`.
   - *Environment secrets*: `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN`. Envie pelo stdin, para o valor não ficar no histórico do shell:
     ```bash
     for f in client_id client_secret refresh_token; do
       python -m scripts.youtube_auth --print-field $f | gh secret set "YT_$(echo $f | tr a-z A-Z)" --env youtube-production
     done
     ```
2. *Settings → Secrets and variables → Actions → Variables*:
   - `YOUTUBE_PUBLISH_ENABLED=true`, só quando tudo estiver pronto;
   - `GOOGLE_DRIVE_FOLDER_ID`;
   - `GCP_WIF_PROVIDER`;
   - `GCP_DRIVE_SA`.
3. *Settings → Branches*: proteja a `main`. Exija PR e o check `ci / checks`, e bloqueie force push.
   - Se a proteção bloquear o push do bot que registra o estado, o job não falha: o registro fica no artefato `publish-record-<id>` por 90 dias. Para manter o registro na `main`, permita que o GitHub Actions ignore a regra.
   - Revise também mudanças em `scripts/` e `.github/` nos PRs, porque é esse código que roda com os secrets depois do merge.
4. *Settings → Code security*: ative **Secret scanning** e **Push protection** (grátis em repositório público).

**Drive sem chave (Workload Identity Federation)**: crie uma conta de serviço sem papéis e compartilhe com ela **só a pasta dos vídeos**, como leitora. Depois:
```bash
gcloud iam workload-identity-pools create github --location=global
gcloud iam workload-identity-pools providers create-oidc github-repo --location=global \
  --workload-identity-pool=github --issuer-uri="https://token.actions.githubusercontent.com" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository,attribute.ref=assertion.ref" \
  --attribute-condition="assertion.repository=='edmilsonve/Projeto-Video' && assertion.ref=='refs/heads/main'"
gcloud iam service-accounts add-iam-policy-binding drive-reader@PROJETO.iam.gserviceaccount.com \
  --role=roles/iam.workloadIdentityUser \
  --member="principalSet://iam.googleapis.com/projects/NUMERO/locations/global/workloadIdentityPools/github/attribute.repository/edmilsonve/Projeto-Video"
```
A condição de atributo garante que **só este repositório, na `main`**, consiga se passar pela conta de serviço.

## 5. Erros comuns

| Erro | Causa provável | O que fazer |
|---|---|---|
| Vídeo "bloqueado como privado" | Projeto sem auditoria | Item 4 da configuração |
| `invalid_grant` | Token revogado, ou expirado (app em "Teste") | Ponha o app em produção e rode `scripts.youtube_auth` de novo |
| `quotaExceeded` / `uploadLimitExceeded` | Cota diária | Espalhe o lote ou peça aumento de cota |
| `insufficientPermissions` na thumbnail | Escopo ou canal não verificado | Verifique o canal; se persistir, reautorize |
| Arquivo não encontrado no Drive | Pasta não sincronizou, ou nome diferente de `video_file` | Confira a pasta e o `metadata.json` |
