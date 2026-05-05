# CORS — produção (QDI)

**Variável:** `CORS_ALLOWED_ORIGINS` (CSV, sem espaços entre vírgulas recomendado para cópia segura).

## Regra de segurança

Nunca combine **`allow_origins=["*"]`** com **`allow_credentials=True`** no FastAPI — é anti-padrão **S-05** do projeto (`security-hardening.mdc`).

## Origens típicas em desenvolvimento

Valores default em `src/infrastructure/config/settings.py` cobrem `localhost`/`127.0.0.1` nas portas do `docker-compose` (API **60000**, Web **60001**, Playwright **3333**, etc.).

## Produção

1. Defina lista explícita: origem do Next (`NEXT_PUBLIC_SITE_URL`) + eventual preview/staging.
2. Reinicie a API após alterar env.
3. Valide no browser (DevTools → rede → cabeçalho `Access-Control-Allow-Origin` na chamada `OPTIONS`/`GET` à API).

Ver também `RUNBOOK_DEPLOY_ROLLBACK.md` (tabela `NEXT_PUBLIC_*`).
