# Instruções para agentes

As regras deste repositório estão em [`CLAUDE.md`](CLAUDE.md) e valem para qualquer agente (Claude Code, Antigravity/agy ou outro).

Resumo:
- O **Claude Code é o único agente que escreve** neste repositório.
- Outros agentes (por exemplo, o Gemini via `agy`) trabalham **só leitura**: respondem em `runs/<id>/agy/result.md` e não fazem commit nem push.
- Nenhum agente lê credenciais, publica no YouTube, faz merge ou altera secrets. Isso é exclusivo de pessoas (veja `docs/SEGURANCA_CREDENCIAIS.md`).
- Provedores permitidos: Claude e Gemini. Não adicione OpenAI nem Groq.
- Nunca simule comportamento humano em plataformas e nunca publique sem merge de PR aprovado.
