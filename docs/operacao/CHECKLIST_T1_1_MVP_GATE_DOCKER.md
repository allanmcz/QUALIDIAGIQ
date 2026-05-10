# Checklist T1.1 — Gate MVP com Postgres no Docker (`make mvp-gate`)

**Objetivo:** provar que o **mesmo** Postgres exposto pelo `docker-compose.yml` em desenvolvimento (imagem **pgvector/pgvector:pg16**, migrações aplicadas) passa no gate automatizado e na verificação de schema **strict**, **sem** depender de Supabase cloud para o MVP.

**Consolidado em:** [`CHECKLIST_IMPLEMENTACAO_MVP_POS_DOCKER_DEV.md`](./CHECKLIST_IMPLEMENTACAO_MVP_POS_DOCKER_DEV.md) §T1.1.

**Referências:** `Makefile` (`mvp-gate`, `verify-schema-mvp-strict`), `scripts/verify_mvp_schema.py`, `.env.example` (secção testes / gates).

---

## Metadados da execução (preencher ao concluir)

| Campo | Valor |
|-------|--------|
| Data (UTC ou America/Sao_Paulo) | **2026-05-10** · ~19:27–19:32 (−03, America/Sao_Paulo) |
| Operador | **Allan Marcio** |
| `git rev-parse --short HEAD` | **`328b13e`** |
| Postgres efectivo (host:porta) | **`127.0.0.1:60322`** (Compose → serviço `qdi-db`) |

---

## Pré-requisitos

- [x] Repositório actualizado (`git status` limpo ou alterações conhecidas).
- [x] Python venv do projeto (`make install` se necessário).
- [x] Docker / OrbStack em execução.

---

## Passo 1 — Subir o Postgres do projeto

Escolha **uma** das opções:

- [x] **A.** Stack completa de dev: `make dev`
- [ ] **B.** Só base de dados: `docker compose up -d db`

**Confirmação:**

- [x] Serviço `db` saudável (Compose).
- [x] Porta no host **60322** aceita ligação (típico mapeamento deste repo).

Se a base já existia **antes** de novas migrações no Git:

- [x] Migrações aplicadas: `make migrate` (idempotente sobre ficheiros em `src/infrastructure/db/migrations/`). — *N/A na evidência: volume já inicializado com `init.sql`; DB Healthy.*

---

## Passo 2 — Variáveis de ambiente (Postgres local)

O `Makefile` já exporta defaults para `127.0.0.1:60322` se omitires as variáveis. Para **documentação explícita** na evidência ou shell:

```bash
export QDI_POSTGRES_TEST_URL="${QDI_POSTGRES_TEST_URL:-postgresql://postgres:postgres@127.0.0.1:60322/postgres}"
export DATABASE_URL="${DATABASE_URL:-$QDI_POSTGRES_TEST_URL}"
```

- [x] Variáveis definidas **ou** aceite explícito de usar os defaults do `Makefile`. — *Usados defaults do `Makefile` (`127.0.0.1:60322`).*

**Segurança:** na evidência arquivada, **não** colar URLs com passwords diferentes do exemplo de dev se isso expuser credenciais reais.

---

## Passo 3 — Gate MVP (`pytest` integração focado)

```bash
make mvp-gate
```

O alvo executa (com defaults locais):

- `tests/integration/test_smoke_mvp_fechado_api.py`
- `tests/integration/test_mvp_gate_postgres.py`

- [x] Comando terminou com **exit code 0** (saída verde / sem falhas). — *5 passed em ~2,98 s.*

---

## Passo 4 — Verificação de schema MVP **strict**

```bash
make verify-schema-mvp-strict
```

Inclui validações base + `--strict` CNAE (0013/0014) + normativa score macro (0015).

- [x] Comando terminou com **exit code 0**. — *Saída: verificação MVP schema OK (strict CNAE + normativa 0015).*

---

## Passo 5 — Evidência versionável (sem secrets)

- [x] Registar **data**, **hash Git** e confirmação de que os passos 3–4 foram executados contra **Postgres Docker local** (referência explícita a `127.0.0.1:60322` ou ao mapeamento efectivo **sem** passwords sensíveis).

### Registo arquivado (encerramento Passo 5)

| Item | Detalhe |
|------|--------|
| **Data / fuso** | 2026-05-10, sessão ~19:27–19:34 **America/Sao_Paulo** (−03) |
| **Operador** | Allan Marcio |
| **Git** | `328b13e` (`git rev-parse --short HEAD` na máquina de evidência) |
| **Postgres** | Docker Compose local — **`127.0.0.1:60322`** → contentor **`qdi-db`** (imagem **pgvector/pgvector:pg16**); stack via **`make dev`** (`API /health OK`, `qdi-db Healthy`). |
| **`make mvp-gate`** | **Exit 0** — 5 testes: smoke health/trace + POST lista/detalhe com aceite LGPD; schema `aceite_termos_privacidade_em` (0012); `diagnostico_mutacao_audit` (0026); RLS `authenticated` só vê o próprio tenant. *(~2,98 s no host reportado.)* |
| **`make verify-schema-mvp-strict`** | **Exit 0** — núcleo 0012 + M12 + RLS + `qdi_jwt_tenant_id` + 0026; modo strict CNAE (extensões + 1332 subclasses) + normativa score macro (0015). |
| **Secrets** | Nenhuma credencial de produção neste registo; URL de dev alinhada a `.env.example` / Compose. |

**Onde arquivar (uma das opções):**

- [ ] Secção / bloco datado em [`PDF_HOMOLOGACAO_CHECKLIST_B1.md`](./PDF_HOMOLOGACAO_CHECKLIST_B1.md) **ou**
- [x] Outro artefacto em `docs/operacao/` com prefixo claro (ex.: evidência T1.1) **ou**
- [ ] Ticket interno com mesmo conteúdo e ligação no changelog semanal.

*Arquivamento efectivo:* este ficheiro (**`CHECKLIST_T1_1_MVP_GATE_DOCKER.md`**, Passo 5 e metadados).

**Opcional G3 (pré-go-live público):**

- [ ] Repetir passos 3–4 contra **Supabase gerido** (URL própria) e arquivar **segunda** evidência datada.

---

## Aceite final T1.1

Marque só quando **todos** aplicável:

- [x] `make mvp-gate` verde com Postgres do Docker local.
- [x] `make verify-schema-mvp-strict` OK com a mesma instância.
- [x] Evidência datada arquivada (Passo 5).
- [x] Caixa T1.1 correspondente assinalada em [`CHECKLIST_IMPLEMENTACAO_MVP_POS_DOCKER_DEV.md`](./CHECKLIST_IMPLEMENTACAO_MVP_POS_DOCKER_DEV.md).

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
