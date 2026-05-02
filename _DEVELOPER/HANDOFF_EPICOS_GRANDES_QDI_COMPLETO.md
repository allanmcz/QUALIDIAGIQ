# Handoff — Épicos grandes QDI (PLANO_EXECUCAO_EPICOS_GRANDES_QDI.md)

> Documento de continuidade após implementação da **fatia E1** e registro explícito do backlog **E2–E5**.  
> *(Pasta `_DEVELOPER/` está no `.gitignore`; versionar com `git add -f` quando necessário.)*

## Resumo executivo

| Épico | Estado neste handoff | Observação |
|-------|----------------------|------------|
| **E1** Versionamento normativo do motor de score (PostgreSQL) | **Entregue (MVP técnico)** | Tabela `qdi.normativa_score_macro_dimensao`, ADR-005, wiring no use case + endpoints públicos |
| **E2** MoSCoW SHOULD (Beta) | Não iniciado | 11 features; kickoff por subépico (ver `docs/refs/02_MOSCOW_FEATURES.md`) |
| **E3** MoSCoW COULD (GA) | Não iniciado | Depende Beta estável + billing (D5) |
| **E4** API Enterprise + documentação | Não iniciado | OpenAPI estável, API keys/OAuth, sandbox |
| **E5** Conectores ERP | Não iniciado | Worker/ACL isolado do núcleo QDI |

## E1 — O que foi implementado

- **SQL:** `src/infrastructure/db/migrations/0015_normativa_score_macro_dimensao.sql`  
  - RLS + políticas `authenticated` (SELECT) e `service_role` (ALL).  
  - Seed baseline 2026-01-01 espelhando os pesos que estavam em `PESOS_MACRO_DIMENSAO_SCORE_GERAL`.
- **Domain:** port `NormativaScoreMacroRepository`; invariante `exigir_mapa_pesos_macro_completo` em `score.py`.
- **Infrastructure:** `PostgresNormativaScoreMacroRepository` (psycopg2), `EmbutidasNormativaScoreMacroRepository`.
- **Application:** `CalcularScoreUseCase` recebe o port; parâmetro `data_referencia_normativa`; `RealizarDiagnostico` usa data UTC do servidor.
- **Presentation:** `get_normativa_score_macro_repository`, `pesos_macro_dimensao_iso_para_http`; rotas `/metodologia` e `/manifesto-pesos` alinhadas ao Postgres quando `DATABASE_URL` existe.
- **Verificação ops:** `scripts/verify_mvp_schema.py` em modo estrito (`QDI_VERIFY_SCHEMA_STRICT_CNAE=1`) também valida presência da tabela e **7 dimensões** distintas.

## Data de referência da vigência (decisão explícita)

- **POST `/diagnosticos/`:** `datetime.now(UTC).date()` no momento do cálculo.
- **GET metodologia / manifesto:** mesma regra com “agora” UTC (transparência em tempo real).

Se no futuro o produto exigir **data normativa fixa por diagnóstico** (ex.: competência fiscal), evoluir modelo persistindo `data_referencia_normativa` no agregado e lendo-a no recálculo — fora do escopo desta fatia.

## E2–E5 — Próximos passos sugeridos

1. **E2:** Escolher 1–2 itens SHOULD por trimestre; cada um com kickoff próprio (ex.: “spike S02 RAG Lexiq mínimo”).
2. **E3:** Gate comercial + métricas Beta antes de investir em COULD.
3. **E4:** Separar tier Enterprise em projeto de API keys e contratos SLAs.
4. **E5:** PoC connector em repositório ou serviço apartado (ACL), sem SQL de ERP no domain QDI.

## Referências rápidas

- Plano fonte: `_DEVELOPER/PLANO_EXECUCAO_EPICOS_GRANDES_QDI.md`
- ADR: `.github/adr/ADR-005-normativa-score-macro-postgres.md`
- MoSCoW: `docs/refs/02_MOSCOW_FEATURES.md`

---

*Atualizado na entrega da fatia E1 — QualiDiagIQ.*
