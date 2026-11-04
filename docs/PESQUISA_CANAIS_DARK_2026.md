# Pesquisa: canais dark populares e aderência às 20 dicas (nov/2026)

**Escopo e limites:** a pesquisa foi feita na web em novembro de 2026.
- **Números de inscritos:** vêm de blogs e agregadores, que divergem entre si. Trate-os como ordem de grandeza e confira no Social Blade ou na página do canal.
- **Avaliação de aderência:** é feita pelo formato público de cada canal, e não por uma auditoria vídeo a vídeo.
- **Brasil:** não encontrei um ranking confiável de canais dark brasileiros.

## 1. Canais que cresceram

| Canal | Inscritos (fonte) | Formato | Segue bem | Diferença em relação às dicas |
|---|---|---|---|---|
| 5-Minute Crafts | ~81 mi (blog FlowShorts) | Estúdio (TheSoul), DIY | 4, 14, 16 | Equipe grande de produção física; não é IA |
| DaFuq Boom | ~46,8 mi (blog) | Animação/meme | 7, 12 | Receita citada sem fonte primária |
| Bright Side | ~44,5–44,7 mi (Wikipedia) | Estúdio (TheSoul), curiosidades narradas | 1, 4, 6, 14 | Escala de estúdio |
| WatchMojo | ~26 mi (blog) | Listas narradas | 5, 8, 17 | Equipe editorial própria |
| Incrível (PT-BR) | 18,3 mi (vidIQ, out/2024) | Curiosidades narradas | 1, 4, 6 | Dono não confirmado nas fontes |
| Fatos Desconhecidos (PT-BR) | ~18 mi (fonte antiga) | Curiosidades | 1, 4, 7 | **Tem apresentadores**: é semi-dark |
| HowToBasic | ~17 mi (blog) | Humor absurdo | 4, 7 | Identidade única, não replicável |
| Lofi Girl | 15–20 mi (fontes divergem) | Música e lives contínuas | 15 | Marca e personagem próprios |
| The Infographics Show | ~15 mi (blog) | Animação explicativa | 4, 7, 14 | Equipe de animação |
| Psych2Go | ~13 mi (blog) | Psicologia animada | 2, 19 | Micronicho claro |
| Kurzgesagt | n/d nas fontes | Animação científica | 3, 9, 15 | Os detalhes estão logo abaixo |

**Detalhe do Kurzgesagt:**
- equipe de pesquisa com 6 pessoas, sendo 2 fact-checkers;
- cerca de 1.200 horas por vídeo;
- fontes publicadas;
- removeu 2 vídeos que reconheceu como mal pesquisados;
- a receita vem principalmente de loja e doações.

## 2. Canais encerrados ou desmonetizados

| Caso | O que aconteceu | Regra violada |
|---|---|---|
| Screen Culture e KH Studio | Trailers falsos feitos com IA. Mais de 2 mi de inscritos e mais de 1 bi de views. Desmonetizados; voltaram a monetizar ao rotular "fan-made"; **encerrados** em dez/2025 por spam e metadados enganosos | Dica 3 + divulgação (R4) |
| 16 canais de "AI slop" (análise da Kapwing, reportada em jan/2026) | 35 mi de inscritos e 4,7 bi de views no total. 11 apagados e 5 esvaziados. Exemplos: CuentosFacinantes (~5,9 mi), Imperio de Jesus (quiz religioso, ~5,8 mi), Super Cat League (~4,2 mi), Three Minute Wisdom (~1,7 mi) | Produção em massa (dica 3) |
| Canal de histórias bíblicas com ~588 mil inscritos (fonte única) | Desmonetizado por "conteúdo inautêntico e produzido em massa" | Dica 3 |

## 3. Conclusões aplicadas ao prompt v2

1. **Dicas 3 e 9 são o que separa quem sobrevive.** Os canais que cresceram têm equipe, pesquisa e identidade visual própria. Os encerrados tinham escala sem curadoria. Por isso a v2 exige ângulo, fontes por afirmação, 4 esqueletos de roteiro e revisão humana.
2. **Divulgação protege.** O caso Screen Culture mostra que rotular devolveu a monetização e que deixar de rotular levou ao encerramento. Por isso a v2 usa `containsSyntheticMedia` e o aviso "fan-made".
3. **Nicho não protege.** Gospel e quiz religioso foram atingidos quando produzidos em massa (dica 1 do brief original).
4. **As dicas 4, 6, 7 e 14 aparecem em todos os grandes:** título e thumb fortes, gancho e produção em escala, só que **com equipe**. Na v2, a escala vem do pipeline e a curadoria vem da pessoa.
5. **Dica 15:** a receita própria (loja, apoio do público) é relevante nos grandes, como no Kurzgesagt.
6. **Dica 16:** os grandes estúdios operam em vários idiomas. Hoje a dublagem automática do YouTube permite testar isso antes de abrir um canal novo.
7. **Dica 20:** não encontrei evidência de que "aquecer conta" faça diferença. Nenhum canal de sucesso analisado depende disso, e simular comportamento humano viola os termos. Na v2 ela foi substituída por um checklist manual e uma cadência gradual.
8. **Sinais de satisfação:** fornecedores afirmam que a satisfação virou o sinal "principal" em abril de 2026. Não encontrei o anúncio oficial. O consenso, mais seguro, é que retenção aos 30 s e "título entregue" importam. Ambos foram implementados no QA da v2.

## Fontes

- Canais e números: [awisee](https://awisee.com/blog/successful-faceless-youtube-channels/), [FlowShorts](https://flowshorts.app/blog/best-faceless-youtube-channels), [Wikipedia: Bright Side](https://en.wikipedia.org/wiki/Bright_Side_(YouTube_channel)), [vidIQ: Incrível](https://vidiq.com/youtube-stats/channel/UCIQPHl1WKKTt9KkWyo_JNig), [Fatos Desconhecidos](https://www.youtube.com/user/fatosdesconhecidos), [TecMundo: maiores canais BR](https://www.tecmundo.com.br/internet/412370-20-canais-do-youtube-com-mais-inscritos-no-brasil-conheca.htm)
- Kurzgesagt: [processo oficial](https://kurzgesagt.org/youtube/), [1.200 horas por vídeo](https://rosetta.to/u/kurzgesagt/how-to-make-a-kurzgesagt-video-in-1200-hours), [confiabilidade e correções](https://rosetta.to/u/kurzgesagt/can-you-trust-kurzgesagt-videos)
- Encerramentos: [Tribune: trailers falsos](https://tribune.com.pk/story/2582980/youtube-terminates-ai-generated-fake-movie-trailer-channels-after-policy-breaches), [Film Stories](https://filmstories.co.uk/news/youtube-has-deleted-two-major-channels-which-specialised-in-fake-film-trailers/), [IBTimes: 16 canais](https://www.ibtimes.co.uk/youtube-cracks-down-ai-generated-content-1800213), [NetInfluencer](https://www.netinfluencer.com/youtube-removes-major-ai-slop-channels-with-combined-9-8m-in-estimated-annual-revenue/), [Tribune: 4,7 bi de views](https://tribune.com.pk/story/2589917/youtube-deletes-47-billion-views-worth-of-ai-spam-videos-in-major-platform-crackdown)
- Política de conteúdo inautêntico: [AIR Media-Tech](https://air.io/en/monetization/youtube-monetization-policy-changes-2026-a-complete-dated-timeline), [OutlierKit](https://outlierkit.com/resources/faceless-youtube-channel-demonetized/), [The Next Web](https://thenextweb.com/news/youtube-ai-slop-crackdown-faceless-creators-collateral-damage)
- Satisfação e retenção (fornecedores, não verificado): [OutlierKit](https://outlierkit.com/resources/youtube-viewer-satisfaction-algorithm-2026/), [Virvid](https://virvid.ai/blog/viewer-satisfaction-signals-youtube-2026)
- Recursos do YouTube: [TechCrunch: Made on YouTube 2025](https://techcrunch.com/2025/09/16/youtube-rolls-out-studio-updates-likeness-detection-lip-synced-dubs-creator-collabs-and-more), [Search Engine Journal: A/B de títulos](https://beta.searchenginejournal.com/youtube-adds-title-a-b-testing-and-ask-studio-analytics/556232/), [Uppbeat: Made on YouTube 2026](https://uppbeat.io/blog/creator-news/made-on-youtube-2026-brings-new-youtube-tools-for-editing-earning-and-more)
- API (`containsSyntheticMedia`): [YouTube Data API: revision history](https://developers.google.com/youtube/v3/revision_history), [videos resource](https://developers.google.com/youtube/data/reference/rest/v3/videos)
- Voz: [Microsoft Q&A sobre Edge-TTS](https://learn.microsoft.com/en-us/answers/questions/2088770/are-opensource-edge-tts-free-for-commercial-use), [edge-tts no PyPI](https://pypi.org/project/edge-tts), [Kokoro](https://trelis.substack.com/p/kokoro-text-to-speech)
- YPP no Brasil (blog, confira no Studio): [cut.pro](https://cut.pro/pt-BR/blog/canal-dark-youtube-como-comecar)
