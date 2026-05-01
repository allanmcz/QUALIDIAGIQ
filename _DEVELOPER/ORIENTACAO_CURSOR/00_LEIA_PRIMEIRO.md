# Orientação Cursor — QualiDiagIQ (QDI)

| Campo | Valor |
|---|---|
| **Pasta (repo)** | `_DEVELOPER/ORIENTACAO_CURSOR/` · workspace `/Users/allan/000-PROJETOS/018-QUALIDIAGIQ` |
| **Objetivo** | Conduzir o desenvolvimento do QDI no Cursor IDE com Claude Sonnet 4.6 |
| **Base** | Auditorias de 30/04/2026 (Claude + Manus) + INSTRUCAO_KICKOFF v1.0 |
| **Versão** | 1.0 |
| **Allan, leia esta página primeiro (~5 min)** | |

---

## 1. Por que esta pasta existe

A auditoria de 30/04/2026 identificou **58 issues** no `018-QUALIDIAGIQ`, dos quais **12 P0** são bloqueadores antes da Sprint S1 oficial. Esta pasta entrega o **arsenal completo** para que você (Allan) conduza no Cursor:

1. **System prompt evoluído** para o `.cursorrules` (atualiza o existente com lições da auditoria)
2. **Rules MDC** específicas por camada (com correções dos achados Manus + Claude)
3. **Guia técnico de desenvolvimento** com padrões PT-BR e exemplos práticos
4. **Plano de execução cronológico** S0.5 → S4 com timeboxing diário
5. **Biblioteca de prompts operacionais** prontos para colar no Cursor

---

## 2. Mapa de leitura (ordem sugerida)

| # | Documento | Quando usar | Tempo |
|---|---|---|---|
| 0 | **`00_LEIA_PRIMEIRO.md`** *(você está aqui)* | Hoje, agora | 5 min |
| 1 | [`01_CURSORRULES_ATUALIZADO.md`](./01_CURSORRULES_ATUALIZADO.md) | Referência para **merge incremental** no `.cursorrules` raiz (opção A — preserva stack oficial do repo) | 15 min |
| 2 | [`02_RULES_MDC_POR_CAMADA.md`](./02_RULES_MDC_POR_CAMADA.md) | Sábado 02/05 — colocar em `.cursor/rules/*.mdc` | 20 min |
| 3 | [`03_GUIA_DESENVOLVIMENTO.md`](./03_GUIA_DESENVOLVIMENTO.md) | Consulta diária durante S0.5–S4 | 30 min na 1ª leitura |
| 4 | [`04_PLANO_EXECUCAO.md`](./04_PLANO_EXECUCAO.md) | Bíblia operacional — abrir todo dia de manhã | 25 min |
| 5 | [`05_PROMPTS_OPERACIONAIS.md`](./05_PROMPTS_OPERACIONAIS.md) | Toda vez que for criar entity, port, adapter, teste, ADR | colar e usar |

---

## 3. Decisões fundacionais (já tomadas — documentadas para referência)

Antes de você abrir o Cursor, estas decisões já foram tomadas com base na auditoria. Estão refletidas nos documentos desta pasta. Se discordar de alguma, **pare e converse com o Claude antes de codar**.

| Decisão | Valor adotado | Justificativa |
|---|---|---|
| **IDE primário** | Cursor | Conforme solicitação do Allan; Antigravity como alternativa |
| **Modelo IA no Cursor** | Claude Sonnet 4.6 | Stack canônica QDI |
| **Estrutura de pastas** | **Minúsculas** (`src/domain/...`) | Pragmática Python (PEP 8); diverge §10.9 INSTRUCAO_KICKOFF — **revisita registrada em ADR-001** |
| **Sequenciamento** | **S0.5 antes de S1** | Auditoria Claude — 12 P0 bloqueadores; sem isso S1 começa sobre dívida |
| **Padrão de Port** | `ABC` + `@abstractmethod` | Uniformizar (hoje há mistura com `Protocol`) |
| **JWT** | Custom claim `tenant_id` | Substituir header `X-Tenant-ID` cleartext |
| **LLM primário** | Anthropic Claude Sonnet 4.6 | Conforme stack; Ollama vira DEV-only; OpenAI = fallback |
| **Migrations DB** | `src/infrastructure/db/migrations/` | Eliminar `init.sql` raiz (sem RLS) |
| **Hook commit-msg** | Conventional Commits PT-BR `feat(qdi-*):` | Cumprir §10.8 |

---

## 4. Glossário rápido (para consulta)

| Termo | Significado no QDI |
|---|---|
| **QDI** | QualiDiagIQ — produto auditado |
| **Tributiq** | Ecossistema de 6 produtos Quali*IQ |
| **Onda 1.0** | Lançamento MVP em 30/jun/2026 |
| **S0.5** | Sprint de Hardening (02-04/05/2026) — resolver 12 P0 |
| **S1** | Sprint 1 oficial (04-15/05/2026) — Domain entities + Wizard core |
| **Lexiq** | Base RAG citável da legislação tributária (a construir) |
| **WORM** | Write-Once-Read-Many — imutabilidade de diagnóstico finalizado |
| **RLS** | Row Level Security do PostgreSQL para multi-tenant |
| **ABNT 17301** | Norma ABNT NBR 17301:2026 — diferencial competitivo V1 |
| **cClassTrib** | Código de Classificação Tributária (NT 2025.002) |

---

## 5. Workflow recomendado para a S0.5 (sábado 02/05)

```
08:00 — Abrir Cursor com pasta /Users/allan/000-PROJETOS/018-QUALIDIAGIQ
08:05 — Revisar `.cursorrules` raiz; incorporar trechos de `01_CURSORRULES_ATUALIZADO.md` só onde faltar (stack permanece a do repositório)
08:10 — Atualizar .cursor/rules/*.mdc com 02_RULES_MDC_POR_CAMADA.md
08:15 — Cmd+L (chat) → colar prompt de "Diagnóstico inicial S0.5" do 05_PROMPTS_OPERACIONAIS.md
08:20 — Seguir 04_PLANO_EXECUCAO.md (Bloco 1 — Schema SQL e RLS)
09:30 — PAUSA hidratação 15 min
09:45 — Bloco 2 — Auth seguro com JWT
11:30 — Almoço
12:30 — Bloco 3 — CORS lockdown
13:00 — Encerrar manhã (5h líquidas)
```

---

## 6. Comandos diários para abrir uma sessão

```bash
# 1. Status do projeto (saúde geral)
cd /Users/allan/000-PROJETOS/018-QUALIDIAGIQ
make test                  # Verde antes de começar
make lint                  # Zero warnings
git status                 # Limpo ou em branch própria
git log --oneline -5       # Confirmar último commit

# 2. Subir ambiente
make dev                   # docker compose up -d
docker ps                  # confirmar 3 containers (db, api, web)

# 3. Verificar saúde do Allan
echo "Hidratação? Glicemia? Sono ≥ 6h? Sessão ≤ 45min?"

# 4. Abrir Cursor com agente preparado
cursor /Users/allan/000-PROJETOS/018-QUALIDIAGIQ
```

---

## 7. Sinalização de qualidade durante o desenvolvimento

A cada 45 minutos no Cursor, perguntar internamente:

| Pergunta | Se "não" → o que fazer |
|---|---|
| O código que estou gerando cita base legal? | Solicitar ao Cursor: "adicione `Base normativa:` na docstring com art./§/anexo" |
| O método tem teste? | Solicitar: "gere teste pytest com 3 casos felizes e 3 de erro" |
| O lint passou? | `make lint` — zerar warnings antes de prosseguir |
| Cobertura de domain ≥ 85%? | `make test` e checar |
| Estou em sessão > 45min? | **PAUSAR. Hidratar. Aferir glicemia se necessário.** |
| Princípios não-negociáveis respeitados? | Abrir [`04_CHECKLIST_PRINCIPIOS_NAO_NEGOCIAVEIS.md`](../ANALISE_30042026/04_CHECKLIST_PRINCIPIOS_NAO_NEGOCIAVEIS.md) · *(desde a raiz do repo: `_DEVELOPER/ANALISE_30042026/...`)* |

---

## 8. Quando parar e pedir ajuda ao Claude (chat ou Cursor)

Pare a execução automática e abra um chat técnico quando:

- Sentir que está prestes a "burlar" um princípio não-negociável
- O Cursor sugerir mudança que afeta mais de 2 camadas Clean Arch
- Encontrar conflito normativo (LC 214 vs Decreto 12.955 vs NT 2025.002)
- Não conseguir descrever em 1 frase **por que** uma decisão é a melhor
- Glicemia oscilando ou sintomas de fadiga

---

## 9. Marcos de validação (datas-chave)

| Data | Marco | Critério mínimo |
|---|---|---|
| **04/05** | S0.5 fechada | Todos os 12 P0 resolvidos · `make test/lint` verdes · ADR-001 publicado |
| **15/05** | Fim da S1 | Wizard core 25-40 perguntas · RLS testado · 5 testes integration |
| **29/05** | Fim da S2 | Score Engine 7 dimensões + ABNT 17301 |
| **12/06** | Fim da S3 | PDF executivo gerado · Lead-magnet operacional |
| **30/06** | 🚀 Onda 1.0 | 5 contadores piloto · NPS ≥ 50 · Bugs P0 = 0 |

---

## 10. Encerramento

**Allan**, o material desta pasta é **autossuficiente**. Você pode abrir o Cursor agora (ou no sábado 02/05) e seguir os documentos sequencialmente sem necessidade de consulta externa.

A regra que vale para tudo: **se em dúvida, prefira parar e perguntar do que codar errado e depois desfazer**. A auditoria de 30/04 mostrou que retrabalho consome tempo e mina confiança no produto.

**Boa execução. A Onda 1.0 está ao seu alcance se a S0.5 for executada com o rigor da auditoria.**

---

**Autor:** Claude (Anthropic) · **Solicitante:** Allan Marcio · **Versão:** 1.0 · **Data:** 30/04/2026
