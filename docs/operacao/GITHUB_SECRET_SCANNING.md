# GitHub — Secret scanning e push protection

Estas opções **não** são versionadas no repositório; devem ser ativadas por um administrador no GitHub.

## Passos

1. Repositório → **Settings** → **Code security and analysis**.
2. Ativar **Secret scanning**.
3. Ativar **Push protection** (quando disponível no plano da organização).

Complemento local: hooks em `.githooks/` (`make install-hooks`) e `gitleaks`.
