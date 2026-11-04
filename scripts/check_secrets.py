"""Varre o repositório (ou só o que está no stage) atrás de segredos. Sem dependências.

    python scripts/check_secrets.py            # arquivos versionados (CI)
    python scripts/check_secrets.py --staged   # antes do commit (git hook)
"""
import re
import subprocess
import sys

PATTERNS = {
    "Anthropic API key": r"sk-ant-[A-Za-z0-9_\-]{20,}",
    "Google API key": r"AIza[0-9A-Za-z_\-]{35}",
    "Google OAuth client secret": r"GOCSPX-[A-Za-z0-9_\-]{20,}",
    "Google refresh token": r"1//0[A-Za-z0-9_\-]{30,}",
    "Google access token": r"ya29\.[A-Za-z0-9_\-]{30,}",
    "Chave privada": r"-----BEGIN (?:RSA |EC |OPENSSH |ENCRYPTED )?PRIVATE KEY-----",
    "JSON de conta de serviço": r"\"type\"\s*:\s*\"service_account\"",
    "Token do GitHub": r"(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})",
    "Token da Replicate": r"r8_[A-Za-z0-9]{30,}",
    "Chave genérica sk-": r"\bsk-[A-Za-z0-9]{32,}\b",
}
FORBIDDEN_FILES = r"(^|/)(\.env(\.local)?|client_secret[^/]*\.json|service_account[^/]*\.json|token[^/]*\.(json|pickle)|credentials[^/]*\.json|[^/]*\.(pem|p12|pfx|key))$"


def list_files(staged: bool):
    cmd = ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"] if staged else ["git", "ls-files"]
    return [f for f in subprocess.run(cmd, capture_output=True, text=True, check=True).stdout.splitlines() if f]


def scan(files, read=lambda p: open(p, encoding="utf-8", errors="ignore").read()):
    findings = []
    for path in files:
        if re.search(FORBIDDEN_FILES, path):
            findings.append((path, 0, "arquivo de credencial versionado"))
            continue
        try:
            text = read(path)
        except (OSError, UnicodeDecodeError):
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            for name, pattern in PATTERNS.items():
                if re.search(pattern, line):
                    findings.append((path, lineno, name))
    return findings


def main():
    findings = scan(list_files("--staged" in sys.argv))
    for path, lineno, name in findings:
        print(f"SEGREDO? {path}:{lineno}: {name}")  # nunca imprime o valor
    if findings:
        print("Bloqueado: remova o segredo, revogue-o no provedor e use variáveis de ambiente/secrets.")
        return 1
    print("Nenhum segredo encontrado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
