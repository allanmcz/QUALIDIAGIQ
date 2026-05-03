# Critérios de aceite e evidências — MVP corte **2026-05-05**

Cada linha deve ter **evidência colável**: link, hash de commit, screenshot nomeado, ou trecho de log.

---

## 1. Definição A — MVP 100% técnico (obrigatório mínimo para 05-05)

| # | Critério | Como verificar | Onde registar |
|---|------------|----------------|---------------|
| A1 | `make test` + `make lint` + `make type-check` verdes na branch de release | CI local + job GitHub | Nota no `CHANGELOG` + SHA |
| A2 | `make mvp-gate` verde | Comando na raiz | Saída anexada ou referência CI |
| A3 | `make verify-schema-mvp-strict` (ou script equivalente) no **DB alvo** do corte | `DATABASE_URL` / `QDI_POSTGRES_TEST_URL` | Copiar sumário “ok” para nota interna ou ticket |
| A4 | PDF gerado no **espelho** com: pt-BR + pelo menos um fluxo `locale_relatorio` acordado | `PDF_HOMOLOGACAO_CHECKLIST_B1.md` itens objetivos | Marcar **[x]** no checklist B1 + guardar PDF exemplo (fora do Git se contiver PII) |
| A5 | Smoke manual `SMOKE_MVP_FECHADO.md` executado uma vez no ambiente de corte | Checklist | **[x]** com data nas linhas correspondentes |
| A6 | **Tag Git** + entrada em `docs/CHANGELOG_MVP.md` | `git tag`, diff changelog | Repositório remoto |

---

## 2. Definição **D** — Demo local + consultoria supervisionada (MacBook, sem público)

| # | Critério | Como verificar | Onde registar |
|---|------------|----------------|---------------|
| D1 | `make dev` + fluxo wizard → PDF **no localhost** | Gravação curta ou PDF exemplo | Pasta local (não commitar PII) |
| D2 | `make test` + `make lint` + `make type-check` + `make mvp-gate` na branch usada na demo | Terminal | Nota em `MVP_05052026/` ou ticket |
| D3 | `PDF_HOMOLOGACAO_CHECKLIST_B1.md` — **só** itens objetivos (layout, quebras, contraste, rodapé) | Revisão visual | **[x]** com nota “subset demo local” |
| D4 | **Não** exigir D4, P6 cloud, tag, changelog, parecer jurídico comercial | N/A | Registar em [`00_CENARIO_DEMO_LOCAL_SUPERVISIONADA.md`](./00_CENARIO_DEMO_LOCAL_SUPERVISIONADA.md) §1 |
| D5 | Dados: **fictícios** na demo **ou** base legal clara para dados reais em sessão supervisionada | Checklist mental / termo cliente | Nota privada escritório |

---

## 3. Definição B — Extensões institucionais (se forem exigidas no mesmo corte)

| # | Critério | Como verificar | Onde registar |
|---|------------|----------------|---------------|
| B1 | Parecer jurídico **`/termos`** + **`/privacidade`** | PDF ou e-mail do advogado | `docs/legal/STATUS_JURIDICO_MVP.md` |
| B2 | Retenção telefone + canal titular/DPO | Texto alinhado em `/privacidade` + processo interno | Mesmo + registo interno |
| B3 | RLS no **Supabase cloud** (se não dispensado) | Captura SQL/policies ou nota ops | `CHECKLIST` sec. 1 + `_DEVELOPER/analises/GAP_ANALYSIS_RLS_P6_2026-05-02.md` atualizado |
| B4 | Critério **3 contadores externos** (se MUST comercial) | 3 fichas assinadas ou e-mail | Sec. 5 do `CHECKLIST_CONFIRMACAO_ALLAN_MVP.md` |

---

## 4. Critérios explícitos de **rejeição** (não declarar 100% se)

- PDF “dummy” mascarado como relatório real em ambiente de corte (anti-padrão do plano MVP).  
- `tenant_id` ou segredos fora de env / settings.  
- **Go-live público:** push para produção **sem** rollback documentado (`RUNBOOK_DEPLOY_ROLLBACK.md`). Em **D** não há obrigação de push de prod.  

---

## 5. Após o corte

- [x] Atualizar `_DEVELOPER/HANDOFF_PROXIMA_SESSAO_QDI.md` (§12.3 — P5/P6) com **datas** e **links** das evidências — **feito** 2026-05-05 (MVP-D).  
- [ ] Opcional: PR “release/MVP-2026-05-05” só com docs + tag, sem feature nova (cenário **A**).

---

*Ver cronograma:* [`03_CRONOGRAMA_03A05_MAI_2026.md`](./03_CRONOGRAMA_03A05_MAI_2026.md) · *Cenário D:* [`00_CENARIO_DEMO_LOCAL_SUPERVISIONADA.md`](./00_CENARIO_DEMO_LOCAL_SUPERVISIONADA.md)
