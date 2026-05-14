# ADR-005 — Pesos macro do score geral versionados no PostgreSQL

## Status

Aceito — implementado (migração `0015_normativa_score_macro_dimensao.sql` + port domain + adapters).

## Contexto

O princípio Tributiq de **versionamento normativo** (`vigencia_inicio` / `vigencia_fim`) aplicava-se ao catálogo conceitual, mas os **pesos macro por dimensão** (agregação do score geral, M03) permaneciam apenas como constantes Python (`PESOS_MACRO_DIMENSAO_SCORE_GERAL`).

Sem persistência versionada, mudanças de metodologia exigem deploy de código e dificultam auditoria por data de referência do diagnóstico.

## Decisão

1. Criar a tabela `qdi.normativa_score_macro_dimensao` com vigência e uma linha por dimensão por faixa de vigência.
2. Resolver a vigência efetiva na **data de referência** do diagnóstico com `DISTINCT ON (dimensao) ... ORDER BY vigencia_inicio DESC` (Postgres).
3. Manter **fallback embutido** (`EmbutidasNormativaScoreMacroRepository`) quando `DATABASE_URL` não está configurada (desenvolvimento / testes sem Postgres).
4. Endpoints públicos de metodologia/manifesto usam a **mesma** resolução que o motor (`pesos_macro_publicacao_para_http`), com data UTC corrente, incluindo **rasto** `vigencia_inicio` / `vigencia_fim` / `rotulo_versao` por dimensão no JSON (`pesos_macro_dimensao_normativa`).

## Consequências

- **Positivas:** alteração de pesos macro por período sem redeploy; alinhamento com checklist de auditoria (normativa rastreável).
- **Negativas:** dependência de migração aplicada em ambientes com `DATABASE_URL`; latência extra em metodologia/manifesto (consulta curta ao Postgres).
- **Data-canônica:** o POST `/diagnosticos/` usa `datetime.now(UTC).date()` como referência da vigência no momento do cálculo (documentado no handoff dos épicos grandes).

## Alternativas rejeitadas

- **Somente JSON estático versionado:** menos consultável e sem RLS alinhada ao restante do schema `qdi`.
- **Hardcode eterno:** viola princípio de versionamento normativo para o motor de score.

## Referências

- `_DEVELOPER/PLANO_EXECUCAO_EPICOS_GRANDES_QDI.md` — Épico E1
- `docs/refs/04_METODOLOGIA.md` — agregação por dimensão
- LC 214/2025 — previsibilidade e transparência ao contribuinte
