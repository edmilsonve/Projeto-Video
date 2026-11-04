#!/usr/bin/env sh
# Instala um pre-commit que bloqueia commits com segredos. Rode uma vez: sh scripts/install_git_hooks.sh
set -e
hook="$(git rev-parse --git-dir)/hooks/pre-commit"
printf '#!/usr/bin/env sh\nexec python3 scripts/check_secrets.py --staged\n' > "$hook"
chmod +x "$hook"
echo "pre-commit instalado em $hook"
