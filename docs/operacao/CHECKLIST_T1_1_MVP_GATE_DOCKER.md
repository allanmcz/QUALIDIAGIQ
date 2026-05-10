# Checklist T1.1 — Gate MVP com Postgres no Docker (`make mvp-gate`)

**Objetivo:** provar que o **mesmo** Postgres exposto pelo `docker-compose.yml` em desenvolvimento (imagem **pgvector/pgvector:pg16**, migrações aplicadas) passa no gate automatizado e na verificação de schema **strict**, **sem** depender de Supabase cloud para o MVP.

**Consolidado em:** [`CHECKLIST_IMPLEMENTACAO_MVP_POS_DOCKER_DEV.md`](./CHECKLIST_IMPLEMENTACAO_MVP_POS_DOCKER_DEV.md) §T1.1.

**Referências:** `Makefile` (`mvp-gate`, `verify-schema-mvp-strict`), `scripts/verify_mvp_schema.py`, `.env.example` (secção testes / gates).

---

## Metadados da execução (preencher ao concluir)

| Campo | Valor |
|-------|--------|
| Data (UTC ou America/Sao_Paulo) | |
| Operador | |
| `git rev-parse --short HEAD` | |
| Postgres efectivo (host:porta) | `127.0.0.1:60322` (típico Compose) |

---

## Pré-requisitos

- [ ] Repositório actualizado (`git status` limpo ou alterações conhecidas).
- [ ] Python venv do projeto (`make install` se necessário).
- [ ] Docker / OrbStack em execução.

---

## Passo 1 — Subir o Postgres do projeto

Escolha **uma** das opções:

- [ ] **A.** Stack completa de dev: `make dev`
- [ ] **B.** Só base de dados: `docker compose up -d db`

**Confirmação:**

- [ ] Serviço `db` saudável (Compose).
- [ ] Porta no host **60322** aceita ligação (típico mapeamento deste repo).

Se a base já existia **antes** de novas migrações no Git:

- [ ] Migrações aplicadas: `make migrate` (idempotente sobre ficheiros em `src/infrastructure/db/migrations/`).

---

## Passo 2 — Variáveis de ambiente (Postgres local)

O `Makefile` já exporta defaults para `127.0.0.1:60322` se omitires as variáveis. Para **documentação explícita** na evidência ou shell:

```bash
export QDI_POSTGRES_TEST_URL="${QDI_POSTGRES_TEST_URL:-postgresql://postgres:postgres@127.0.0.1:60322/postgres}"
export DATABASE_URL="${DATABASE_URL:-$QDI_POSTGRES_TEST_URL}"
```

- [ ] Variáveis definidas **ou** aceite explícito de usar os defaults do `Makefile`.

**Segurança:** na evidência arquivada, **não** colar URLs com passwords diferentes do exemplo de dev se isso expuser credenciais reais.

---

## Passo 3 — Gate MVP (`pytest` integração focado)

```bash
make mvp-gate
```

O alvo executa (com defaults locais):

- `tests/integration/test_smoke_mvp_fechado_api.py`
- `tests/integration/test_mvp_gate_postgres.py`

- [ ] Comando terminou com **exit code 0** (saída verde / sem falhas).

---

## Passo 4 — Verificação de schema MVP **strict**

```bash
make verify-schema-mvp-strict
```

Inclui validações base + `--strict` CNAE (0013/0014) + normativa score macro (0015).

- [ ] Comando terminou com **exit code 0**.

---

## Passo 5 — Evidência versionável (sem secrets)

- [ ] Registar **data**, **hash Git** e confirmação de que os passos 3–4 foram executados contra **Postgres Docker local** (referência explícita a `127.0.0.1:60322` ou ao mapeamento efectivo **sem** passwords sensíveis).

**Onde arquivar (uma das opções):**

- [ ] Secção / bloco datado em [`PDF_HOMOLOGACAO_CHECKLIST_B1.md`](./PDF_HOMOLOGACAO_CHECKLIST_B1.md) **ou**
- [ ] Outro artefacto em `docs/operacao/` com prefixo claro (ex.: evidência T1.1) **ou**
- [ ] Ticket interno com mesmo conteúdo e ligação no changelog semanal.

**Opcional G3 (pré-go-live público):**

- [ ] Repetir passos 3–4 contra **Supabase gerido** (URL própria) e arquivar **segunda** evidência datada.

---

## Aceite final T1.1

Marque só quando **todos** aplicável:

- [ ] `make mvp-gate` verde com Postgres do Docker local.
- [ ] `make verify-schema-mvp-strict` OK com a mesma instância.
- [ ] Evidência datada arquivada (Passo 5).
- [ ] Caixa T1.1 correspondente assinalada em [`CHECKLIST_IMPLEMENTACAO_MVP_POS_DOCKER_DEV.md`](./CHECKLIST_IMPLEMENTACAO_MVP_POS_DOCKER_DEV.md).

---

## Falhas frequentes (sanidade)

| Sintoma | Verificar |
|---------|-----------|
| Connection refused em `60322` | `docker compose ps`; subir `db`; confirmar mapeamento de portas no `docker-compose.yml`. |
| Erros de migração / coluna em falta | `make migrate`; volume Postgres novo vs antigo (bootstrap `init.sql` só em volume **inicial**). |
| `mvp-gate` falha mas `make test` passa | Gate é **subconjunto** de integração — ler traceback do pytest indicado no Makefile. |
| `verify-schema-mvp-strict` falha em CNAE/normativa | Strict activa flags em `scripts/verify_mvp_schema.py`; confirmar seeds/migrações 0013–0015 aplicadas. |

---

**Última revisão deste checklist:** 2026-05-10.
