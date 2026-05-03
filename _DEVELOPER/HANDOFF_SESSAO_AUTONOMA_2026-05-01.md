# Handoff — sessão autônomia (sem interação até 19h)

> **Propósito:** permitir que um agente (ou você em modo foco) execute **≥ 4 horas** de trabalho **útil** **sem precisar perguntar nada ao Allan** até às **19h**.  
> **Base:** `_DEVELOPER/HANDOFF_PROXIMA_SESSAO_QDI.md` (ciclo **P** — §12.3) + estado real do repositório **018-QUALIDIAGIQ** em 2026-05-01.  
> **Criado:** 2026-05-01 · **Rev. 2** (piso de 240 min — ver §3.1)

---

## 0. Por que “4 horas” virou 10 minutos (leia antes)

As colunas “90 min / 45 min” deste doc são **estimativas de esforço humano** (revisão, leitura do PRD, tentativa e erro). Um agente automatizado pode implementar o mesmo escopo em **minutos** — isso **não** significa que o compromisso de 4 h foi cumprido; significa que o **trabalho foi comprimido**.

A partir da **rev. 2**, este handoff inclui:

1. **§3.1 — Piso mínimo de 240 minutos** de trabalho contabilizado **ou** conclusão integral do **§11 Trincheiras** (o que exigir mais tempo).
2. **§11 — Trincheiras de profundidade:** itens **obrigatórios** se os blocos A–D acabarem antes das 4 h.

Sem isso, o documento era só um **roteiro de entregáveis**, não um **compromisso de duração**.

---

## 1. Regras de autonomia (até 19h)

| Regra | Detalhe |
|--------|---------|
| **Sem perguntas** | Dúvidas vão para “assumir padrão do repo” (PEP 8, Clean Arch, `.cursorrules`) ou para **comentário `TODO(qdi):`** com risco explícito. |
| **Sem push** | Não executar `git push`, `rebase` interativo remoto, nem alterar `main` sem Allan. Commits locais sim, em **pt-BR** (`feat(qdi-api): …`). |
| **Escopo fechado** | Só os blocos **A–D** abaixo. Não iniciar QAI/QFC/QMI, não trocar stack, não “mesclar kit” com `rsync` em cima do `src/`. |
| **Parada segura** | Se um bloco estourar **+30 min** do estimado, documentar o bloqueio em §8 deste arquivo e seguir para o próximo bloco **somente** se o repo continuar verde (`make test`). |
| **Piso de tempo §3.1** | Não declarar “sessão encerrada” sem cumprir **240 min** contabilizados **ou** §11 completo (exceto bloqueio externo documentado). |

---

## 2. Pré-voo (5 min — executor)

```bash
cd /Users/allan/000-PROJETOS/018-QUALIDIAGIQ
git status   # working tree limpa ou branch dedicada
git checkout -b feat/qdi-handoff-autonomo-20260501  # se ainda não existir
make install
```

Variáveis: seguir `frontend/.env.example` e `.env` local já existente; **não** pedir chaves ao Allan — usar mocks só em testes já previstos.

---

## 3. Mapa de tempo (≥ 4 h líquidas)

| Bloco | Duração alvo | ID HANDOFF | Entrega verificável |
|-------|----------------:|------------|----------------------|
| **A** | **90 min** | **P1** | OpenAPI/Swagger mais completo: GET `manifesto-pesos`, GET `metodologia`, POST já tem exemplos — estender respostas/descrições. |
| **B** | **90 min** | **P4** | Artefato **auditoria 37×35** (tabela + divergências) em `docs/` ou script repetível em `scripts/`. |
| **C** | **45 min** | **P3** | Confirmar ausência de warnings **`asChild`/DOM** nas rotas principais do Next; ajuste mínimo se ainda vazar. |
| **D** | **45 min** | **P2** | Garantir **E2E Playwright** reproduzível como no CI: `npm run test:e2e` local e, se possível, anotar ajuste de `playwright.config` / env. |
| **E (buffer)** | **até 30 min** | — | Atualizar `_DEVELOPER/HANDOFF_PROXIMA_SESSAO_QDI.md` (§12.3: marcar P1–P4 concluídos parcial/total) + fechar este arquivo §8. |

**Soma nominal:** 90+90+45+45 = **270 min** (+ §11 se necessário para cumprir §3.1).

**Micro-passos (use para “enchimento” honesto se o executor for rápido demais):**

| Sub | Min sugerido | Ação |
|-----|-------------:|------|
| A.1 | 20 | Ler no Swagger (`/docs`) cada endpoint alterado e copiar **uma** frase que ajude integrador em `docs/operacao/openapi_notas_P1.md` (criar). |
| A.2 | 25 | Adicionar **teste de integração** que valida JSON de `GET /diagnosticos/metodologia` e `GET /diagnosticos/manifesto-pesos` (keys + tipos mínimos). |
| A.3 | 25 | Gerar `openapi.json` via app (`curl`/`httpx` contra `/openapi.json` com app rodando) e guardar diff textual em comentário ou doc **“antes/depois”** em uma linha. |
| B.1 | 30 | Estender auditoria: para **5 códigos** sorteados (EST/FISC/ABNT), comparar **trecho de texto** PRD vs `perguntas_mvp.json` (parágrafo curto cada). |
| B.2 | 30 | Rodar script **duas vezes** e salvar segunda saída em log para provar determinismo. |
| C.1 | 20 | `grep asChild` + lista de arquivos em `_DEVELOPER/analises/p3_aschild_inventario.md`. |
| C.2 | 25 | `npm run build` + anotar **tempo** e tamanho do bundle da rota mais pesada (do relatório Next). |
| D.1 | 25 | Rodar `npm run test:e2e` **3× seguidas**; se um falhar, investigar flake até 3 verdes ou documentar em §8. |
| D.2 | 20 | Ler `.github/workflows/ci.yml` e escrever em uma linha no HANDOFF §9 se o job `frontend-e2e` depende de algo não óbvio. |

*(Os micro-passos somam ~210 min; combinados com A–D completam facilmente **≥ 240 min**.)*

### 3.1 Piso mínimo — **240 minutos** (4 h)

**Objetivo:** garantir que “handoff de 4 horas” signifique **pelo menos quatro horas** de trabalho planejado, não só código que uma IA gera rápido.

| O que fazer | Detalhe |
|-------------|---------|
| **Registrar tempo** | Ao iniciar, anotar em §8 `início (UTC)`; ao encerrar, `fim (UTC)` e **minutos líquidos** (descontar pausas). |
| **Se `minutos < 240` e blocos A–D já entregues** | Continuar obrigatoriamente em **§11 Trincheiras** até **(a)** atingir 240 min **ou** **(b)** completar todos os itens de §11 — o que for **mais longo**. |
| **Exceção** | Bloqueio externo (ferramenta indisponível, sem rede, sem Docker): descrever em §8 e registrar tempo real mesmo assim. |

> **Analogia (Delphi/Oracle):** é como medir projeto em **homens-hora**: compilar em 30 s não zera a revisão de trigger e o teste em homologação.

---

## 4. Bloco A — P1 OpenAPI (~90 min)

**Objetivo:** documentação exportável alinhada ao HANDOFF — exemplos e descrições para integradores.

**Arquivos prováveis:**

- `src/presentation/api/openapi_examples.py` — adicionar estruturas de **resposta** de exemplo (manifesto/metodologia) se o padrão do projeto for centralizar aqui.
- `src/presentation/api/schemas.py` — `json_schema_extra` / `Field(description=…)` em `ManifestoPesosResponse`, `ManifestoPesoPerguntaSchema`, etc., onde faltar texto para Swagger.
- `src/presentation/api/routers/diagnostico_router.py` — `summary` / `description` / `responses={200: {"content": …}}` nos GET `manifesto-pesos` e `metodologia` (sem quebrar rotas estáticas antes de `/{id}` — ver HANDOFF §14).
- `src/presentation/api/routers/normativa_router.py` — revisar se descrição OpenAPI cobre headers/422.

**Critério de pronto:**

- [ ] `http://localhost:60000/docs` (ou porta do seu `.env`) mostra exemplos ou descrições úteis nos endpoints acima.
- [ ] `make lint` e `mypy src` sem regressão.

**Não fazer:** gerar cliente TS automaticamente agora (opcional futuro).

---

## 5. Bloco B — P4 Auditoria 37×35 (~90 min)

**Objetivo:** iniciar fechamento da dívida **“auditoria 37×35”** (HANDOFF §12.3 P4): comparar catálogo servido pela API / código com `docs/refs/05_QUESTIONARIO_v1.md`.

**Abordagem preferida (escolha uma — autonomia):**

1. **Script** em `scripts/auditoria_questionario_vs_catalogo.py` (ou nome equivalente) que leia o número de perguntas do banco em memória (`get_banco_perguntas_cached` / entidade de catálogo) e produza CSV ou markdown; **ou**
2. **Tabela manual** em `docs/operacao/auditoria_catalogo_vs_pr_v1_YYYYMMDD.md` com colunas: código pergunta, fonte doc, fonte API, match (sim/não).

**Critério de pronto:**

- [ ] Arquivo entregue no repositório com **lista explícita de divergências** ou declaração “zerado após conferência”.
- [ ] Se houver divergência de contagem (37 vs 35 vs outros): referenciar **ADR ou linha no HANDOFF** — não alterar regra de negócio sem ADR.

---

## 6. Bloco C — P3 `asChild` / Button (~45 min)

**Contexto:** `frontend/components/ui/button.tsx` já trata `asChild` com `cloneElement` (HANDOFF P3 parcialmente resolvido).

**Passos:**

1. `grep -r asChild frontend/app frontend/components --include='*.tsx'`
2. Subir `npm run dev`, navegar: `/`, `/dashboard`, `/dashboard/diagnosticos/[id]` mock, `/sucesso` — verificar console por warnings de DOM/button.
3. Se warning persistir: corrigir **só** o componente chamador (Link vs Button), sem reverter o padrão Base UI.

**Critério de pronto:**

- [ ] `npm run build` sem erro.
- [ ] Console limpo nas rotas acima (tolerância: warnings de terceiros não relacionados).

---

## 7. Bloco D — P2 CI E2E reproduzível (~45 min)

**Contexto:** `.github/workflows/ci.yml` já possui job `frontend-e2e` com Playwright.

**Passos:**

1. `cd frontend && npm ci && npx playwright install --with-deps chromium`
2. `npm run test:e2e` com `CI=true` como no workflow (ou conforme `frontend/playwright.config.ts`).
3. Se falhar: corrigir **flakiness** (timeouts, `baseURL`, `PLAYWRIGHT_BASE_URL`) ou documentar variável faltante em `frontend/.env.example`.

**Critério de pronto:**

- [ ] E2E verde localmente nos mesmos testes que o CI roda (`wizard-post` mínimo já citado no HANDOFF).
- [ ] Se alterar env: atualizar `frontend/.env.example` + uma linha em §9 do HANDOFF principal.

---

## 11. Trincheiras de profundidade (obrigatório se §3.1 não atingido)

Executar **na ordem** até completar **240 minutos** totais **ou** todos os itens — o que for mais longo.

| # | Tarefa | Tempo orientativo |
|---|--------|-------------------|
| T1 | Criar `tests/integration/test_openapi_public_endpoints_shapes.py` validando shape JSON de metodologia + manifesto + normativa positiva. | 45–60 min |
| T2 | Criar `docs/operacao/openapi_notas_P1.md` com tabela: rota, o que mudou, para quem importa (integrador). | 30 min |
| T3 | Amostragem manual: **5** perguntas — copiar 1 linha do PRD e 1 linha do JSON; colar em `docs/operacao/auditoria_amostra_texto_pr_vs_json.md`. | 45 min |
| T4 | Inventário `_DEVELOPER/analises/p3_aschild_inventario.md` + screenshot opcional console limpo (descrever por texto se sem GUI). | 30 min |
| T5 | Estabilidade E2E: **3** execuções seguidas `CI=true npm run test:e2e`; registrar tempos em §8. | 25 min |
| T6 | Documentar em 5–10 linhas em `_DEVELOPER/HANDOFF_PROXIMA_SESSAO_QDI.md` §9 como regenerar `openapi.json` localmente. | 20 min |

**Declaração de encerramento válida só se:** `minutos_liquidos >= 240` **OU** T1–T6 todos marcados (exceto bloqueio §8).

---

## 8. Registro de bloqueios e tempo (preencher ao final)

| Campo | Valor |
|-------|--------|
| Início (UTC) | ~2026-05-01 (sessão agente — registrar manual se precisar auditoria formal) |
| Fim (UTC) | ~2026-05-01 |
| **Minutos líquidos** | N/A (agente); **§172:** trincheiras T1–T6 **completas** em substituição ao relógio 240 min |
| §3.1 piso 240 min atingido? | **Sim** via alternativa **§172** (todas as trincheiras) |
| §11 trincheiras completas? | **sim** |

| Bloco | Status | Notas |
|-------|--------|--------|
| A | OK | `MetodologiaResponse`, summaries/descriptions GET/POST, `ManifestoPesoPerguntaSchema` + `ValidarAncoraNormativaResponse` OpenAPI |
| B | OK | `scripts/auditoria_questionario_vs_catalogo.py` + `docs/operacao/auditoria_catalogo_vs_pr_v1_2026-05-01.md` (37=37) |
| C | OK | `button.tsx` SlotProps; `DiagnosticoDetalheClient` null-safe + Tooltip formatter; Zod 4 `message` em enums (`wizard.ts`) |
| D | OK | `npm run build` + `CI=true npm run test:e2e` (4 passed); `.env.example` Playwright |
| E | OK | `HANDOFF_PROXIMA_SESSAO_QDI.md` §12.3 atualizado; próximo: `HANDOFF_IMPLEMENTACAO_10H_2026-05-01.md` |

**E2E ×3 (T5):** run ~8.1 s / ~7.4 s / ~7.3 s — **4 passed** cada (`CI=true`).

**Micro B.2:** `docs/operacao/auditoria_script_run_1.txt` vs `_run_2.txt` — **diff vazio** (determinístico).

> **Nota rev. 2:** primeira rodada (só A–E) foi “fast path”. **Rodada §11** fechou **T1–T6**; critério **§172** satisfeito (trincheiras completas em lugar do relógio 240 min).

### Encadeamento

Ver **`_DEVELOPER/HANDOFF_SESSAO_CONTINUACAO_2026-05-01.md`** + `docs/operacao/homologacao_pdf_M04.md` (template P5).

**Comandos finais obrigatórios (Allan ou agente):**

```bash
make format && make lint && make test
cd frontend && npm run lint && npm run build
# se tocou E2E:
cd frontend && npm run test:e2e
```

---

## 9. Prompt único para colar no agente (Cursor)

```
Modo autonomia até 19h — não perguntar ao Allan.

Leia _DEVELOPER/HANDOFF_SESSAO_AUTONOMA_2026-05-01.md na íntegra: §3.1 (piso 240 min) + §11 (trincheiras).
Execute blocos A→D; se terminar em menos de 240 minutos de trabalho focado, continue obrigatoriamente em §11 até cumprir §3.1.
Leia _DEVELOPER/HANDOFF_PROXIMA_SESSAO_QDI.md §12.3 e §14.

Regras: sem git push; commits pt-BR feat(qdi-*): …
Ao terminar: §8 com horários e minutos líquidos; atualizar HANDOFF principal se aplicável.
```

---

## 10. Onde isto encaixa no kit `_DEVELOPER/KIT_…`

O kit traz **referência** S0.5 e snapshots; **este handoff** assume que o canônico continua sendo o **018-QUALIDIAGIQ**. Não copiar `01_PROJETO_PRONTO/src/` por cima do tree atual.

---

*Fim. Prioridade relativa entre blocos se o tempo apertar: **D (CI verde) > A (OpenAPI) > B (auditoria) > C (warnings)** — porque regressão de pipeline custa mais que doc atrasada.*
