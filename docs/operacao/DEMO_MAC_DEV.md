# Demonstração e desenvolvimento no macOS (deadline operacional: **10/05/2026**)

Objetivo: ambiente local **previsível** para **testes reais** (Postgres + API + Next) e **demo** do fluxo LGPD no painel (solicitação → deferimento → anonimização técnica).

## 1. Pré-requisitos

- Docker Desktop ou OrbStack (Compose).
- Python 3.12+ com `poetry` / `.venv` do repositório (`make install`).
- Node 20+ para o frontend (`cd frontend && npm install`).

## 2. Subir stack de desenvolvimento

Na raiz do repositório:

```bash
make dev
# ou: docker compose up -d
```

Serviços típicos:

| Serviço | Porta no Mac | Nota |
|--------|----------------|------|
| API FastAPI | **60000** | Base dos `fetch` do painel em dev (`getApiUrlForFetch`) |
| Postgres | **60322** | Mesmo DSN usado em testes de integração (`QDI_POSTGRES_TEST_URL`) |
| Mailpit | 8025 | UI de e-mail dev |
| Next (compose `web`) | **60001** | Opcional; ver secção 4 |

Aplicar migrações em bases já existentes (volume persistente):

```bash
make migrate
```

Garante entre outras a migração **0029** (`lgpd_anonimizacao_log` + WORM para anonimização).

## 3. Mac: IPv6 / «Failed to fetch»

O projeto documenta em `frontend/lib/api/config.ts` que **`localhost` pode resolver para IPv6** enquanto o Docker publica em IPv4. Preferir:

- **API:** `http://127.0.0.1:60000`
- **Postgres (testes):** `127.0.0.1:60322`

## 4. Front: duas formas de trabalhar

**A) Next no host (recomendado para iteração rápida no Cursor)**

```bash
cd frontend
npm run dev
# abre em http://127.0.0.1:3010 — a API em dev usa 127.0.0.1:60000 automaticamente
```

**B) Next no container Compose (porta 60001)**

- Alinhar `NEXT_PUBLIC_API_URL` com o proxy do container se necessário.
- O código já tenta contornar falhas de proxy em desenvolvimento.

## 5. Roteiro de demonstração (LGPD + painel)

1. Login com conta na plataforma (`/login`) — JWT no `localStorage` (`admin_token`).
2. **Diagnóstico finalizado** com respondente preenchido (wizard com sessão ou gravação self-service + vincular, conforme regras de produto).
3. Abrir **Privacidade LGPD** — ` /dashboard/privacidade` (menu do painel).
4. **Registar** solicitação tipo **anonimização**; colar o **UUID** do diagnóstico.
5. Na lista, alterar status para **deferida** e gravar.
6. Clicar **Executar anonimização** (ou no detalhe do diagnóstico, secção *Privacidade LGPD*).
7. Verificar no Postgres: tabela `lgpd_anonimizacao_log`, `respondente_email` no padrão `anon+{uuid_sem_hífen}@invalid.qdi`, solicitação em `concluida`.

## 6. Testes com Postgres real

Integração backend (executor LGPD):

```bash
# Postgres a escuta em 60322 (Compose)
poetry run pytest tests/integration/test_lgpd_anonimizacao_executor_postgres.py -v --tb=short
```

Opcional: `QDI_POSTGRES_TEST_URL=postgresql://postgres:postgres@127.0.0.1:60322/postgres`

Suite completa:

```bash
make lint && make format && make type-check && make test
```

## 7. Checklist rápido antes de demo externa

- [ ] `docker compose ps` — `db` healthy, `api` up  
- [ ] `make migrate` (se volume antigo)  
- [ ] Login painel OK  
- [ ] Endpoint `/health` ou página inicial carrega  
- [ ] Fluxo LGPD (secção 5) sem erro 503 — API com `DATABASE_URL`/`sync_database_url` válidos para Postgres LGPD  

---

**Referências:** `.cursor/rules/qdi-gravacao-diagnostico-email.mdc`, migração `0029_lgpd_anonimizacao_log_worm.sql`, router `privacidade_router.py`.
