"""Autorização única do canal (rode no SEU computador, uma vez).

    python -m scripts.youtube_auth --client-secret ~/Downloads/client_secret_xxx.json

- Abre o navegador para você autorizar só o escopo youtube.upload.
- Grava client_id, client_secret e refresh_token em ~/.config/darkstudio/youtube.json (0600),
  FORA do repositório. Depois você pode apagar o client_secret baixado.
- Para usar no GitHub Actions, envie cada valor para os secrets do ambiente protegido
  (o comando lê do stdin, então o valor não aparece no histórico do shell):
      python -m scripts.youtube_auth --print-field refresh_token | gh secret set YT_REFRESH_TOKEN --env youtube-production
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.youtube_publisher import LOCAL_CREDENTIALS, SCOPES  # noqa: E402


def authorize(client_secret_path: str):
    from google_auth_oauthlib.flow import InstalledAppFlow

    flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, scopes=SCOPES)
    creds = flow.run_local_server(port=0, prompt="consent", access_type="offline")
    if not creds.refresh_token:
        raise SystemExit("O Google não devolveu refresh_token; revogue o acesso em "
                         "myaccount.google.com/permissions e tente de novo.")
    os.makedirs(os.path.dirname(LOCAL_CREDENTIALS), mode=0o700, exist_ok=True)
    fd = os.open(LOCAL_CREDENTIALS, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump({"client_id": creds.client_id, "client_secret": creds.client_secret,
                   "refresh_token": creds.refresh_token}, f)
    print(f"Credenciais gravadas em {LOCAL_CREDENTIALS} (permissão 600).")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--client-secret", help="JSON do cliente OAuth (tipo 'App para computador')")
    parser.add_argument("--print-field", choices=["client_id", "client_secret", "refresh_token"],
                        help="imprime um campo para enviar via pipe ao 'gh secret set'")
    args = parser.parse_args()
    if args.print_field:
        with open(LOCAL_CREDENTIALS, encoding="utf-8") as f:
            sys.stdout.write(json.load(f)[args.print_field])
        return
    if not args.client_secret:
        parser.error("informe --client-secret")
    authorize(args.client_secret)


if __name__ == "__main__":
    main()
