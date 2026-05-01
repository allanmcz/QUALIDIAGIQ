# Sumário Executivo — Análise Técnica 018-QUALIDIAGIQ

| Campo | Valor |
|---|---|
| **Documento** | Sumário executivo da auditoria técnica do sandbox `018-QUALIDIAGIQ` |
| **Data da análise** | 30 de abril de 2026 |
| **Auditor** | Claude (Mentor + Arquiteto + Pair Programmer) |
| **Versão do código analisado** | commit `353ab73` (feat: B2B auth + JWT) |
| **Escopo** | Backend Python (Clean Arch), Frontend Next.js, Schema SQL, Tests, Configuração |

---

## Veredicto geral

**Nota global: 64/100 — Nível INTERMEDIÁRIO**

| Camada / Aspecto | Nota | Observação |
|---|---:|---|
| Domain (entities + value objects) | **82** | Mais maduro do projeto — Clean Arch respeitada, invariantes claros |
| Application (use cases + ports) | **66** | Funciona, mas viola Clean Arch em pontos críticos (acesso a filesystem) |
| Infrastructure (adapters) | **58** | Implementação ingênua, `print()` em produção, schemas SQL divergentes |
| Presentation (FastAPI) | **52** | Múltiplas vulnerabilidades (SECRET hardcoded, CORS aberto, sem JWT no tenant) |
| Frontend (Next.js) | **70** | Razoável; mocks no lugar errado, ZodResolver antigo, wizard com 3 perguntas vs 35 prometidas |
| Testes (cobertura/profundidade) | **60** | 54 testes; cobertura DOMAIN razoável mas integration/E2E rasos |
| Configuração / DevOps | **68** | Docker, Makefile e pyproject sólidos; commits em inglês violam padrão |
| Documentação | **62** | Boas refs, mas inconsistência com INSTRUCAO_KICKOFF |

**Status geral:** o projeto está em **MVP funcional rudimentar** mas **NÃO está pronto** para os princípios não-negociáveis declarados na INSTRUCAO_KICKOFF (RLS efetivo, idempotência, WORM, RAG citável, score auditável). Dos **12 princípios não-negociáveis**, apenas **3 estão satisfeitos** e **1 está parcialmente atendido**.

---

## Top 10 issues bloqueadores (P0 — antes da S1)

1. **SECRET_KEY de JWT hardcoded** em `auth_router.py:10` (`"qualidiagiq-super-secret-key-dev"`) — risco crítico de segurança
2. **`/auth/create_admin` SEM autenticação** — qualquer anônimo cria admin
3. **`tenant_id` extraído de header HTTP cleartext** sem JWT verification — IDOR direto, RLS inviável
4. **RLS policy usa `auth.uid()`** mas adapter usa anon key sem JWT do tenant — RLS não isolará nada na prática
5. **Bug runtime crítico** em `consultoria_service.py:44` → `PorteEmpresa.MEDIA` não existe (enum tem `MEDIO`) — AttributeError em qualquer empresa porte médio/grande
6. **Schemas SQL duplicados e divergentes** (`init.sql` raiz vs `001_initial_schema.sql`) — `init.sql` não tem RLS habilitado
7. **CORS `allow_origins=["*"]` + `allow_credentials=True`** — combinação incompatível e perigosa
8. **Acesso a filesystem na camada Application** (`realizar_diagnostico.py:124`) lendo `_DEVELOPER/...` — quebra Clean Architecture e quebrará no Docker
9. **Princípio §10.3 violado** — nenhum endpoint POST tem `Idempotency-Key`
10. **Princípio §10.8 violado** — todos os 14 commits estão em inglês ("feat:", "fix:") sem escopo `qdi`

---

## Top 5 lacunas estratégicas (vs. INSTRUCAO_KICKOFF)

| # | Lacuna | Impacto |
|---|---|---|
| L-1 | **Apenas 3 perguntas hardcoded** no router e no Frontend (vs. 25-40 ou 35 prometidas) | Questionário não é "adaptativo" — viola V1 dos vetores de diferenciação |
| L-2 | **RAG sobre Lexiq inexistente** — usa Ollama local lendo arquivo .txt direto do disco | Viola V2 dos vetores; viola §10.7 (citação obrigatória) |
| L-3 | **Score com pesos hardcoded** em duas localidades distintas (com valores divergentes!) | Viola §10.2 (versionamento normativo) e §10.11 (auditabilidade) |
| L-4 | **Sem WORM/SHA-256** em diagnóstico finalizado | Viola §10.4 (imutabilidade) |
| L-5 | **Sem OpenTelemetry instrumentado** apesar do `pyproject.toml` declarar deps | Viola §10.5 (observabilidade) |

---

## Recomendação executiva

Antes de prosseguir para a S1 (04/05/2026), executar uma **Sprint S0.5 de Hardening (3 dias úteis, ~16h)** focada exclusivamente em:

1. Resolver os 10 P0 bloqueadores (segurança + bugs runtime + Clean Arch)
2. Consolidar schemas SQL em fonte única com RLS efetivo
3. Substituir tenant header cleartext por JWT custom claim
4. Unificar enum `PorteEmpresa` e refatorar `consultoria_service`
5. Reescrever os 3 últimos commits seguindo Conventional Commits PT-BR

Sem essa S0.5, a S1 começará sobre **dívida técnica fundacional** que custará mais tempo a remediar em S2/S3.

---

## Próximos documentos

- **`01_ANALISE_DETALHADA.md`** — análise camada-a-camada com citações de linha e código
- **`02_REGISTRO_ISSUES.md`** — registro numerado de 47 issues classificados (P0/P1/P2/P3)
- **`03_PLANO_ACAO_S05_HARDENING.md`** — plano executável da Sprint S0.5 (3 dias)
- **`04_CHECKLIST_PRINCIPIOS_NAO_NEGOCIAVEIS.md`** — auditoria dos 12 princípios um-a-um

---

**Autor:** Claude (Anthropic) · **Solicitante:** Allan Marcio · **Última atualização:** 30/04/2026
