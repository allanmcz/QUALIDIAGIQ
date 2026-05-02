# Smoke Ops — Supabase (evidência P6 / C5)

Roteiro **copiar/colar** para validar schema MVP no projeto Supabase alvo (não substitui go-live comercial).

## Pré-requisitos

- CLI Supabase ou SQL Editor no dashboard do projeto.
- URL do Postgres do projeto (pooler ou direto) exportada como `DATABASE_URL` **sync** no host onde rodar `make`.

## Passos

1. **Schema local de referência**
   ```bash
   cd /caminho/018-QUALIDIAGIQ
   make verify-schema-mvp-strict
   ```
   Corrige drift antes de comparar com a nuvem.

2. **Aplicar migrações no projeto alvo**
   - Executar, **na ordem lexical**, os arquivos em `src/infrastructure/db/migrations/*.sql` no SQL Editor do Supabase (ou pipeline de migração aprovado).

3. **Conferir objetos MVP**
   - Tabelas `admins`, `diagnosticos` e políticas RLS esperadas (ver `0002`–`0005`).
   - Extensões/`qdi.*` conforme migrações CNAE se o escopo MVP as incluir.

4. **Evidência datada**
   - Capturar **screenshot** do SQL Editor com resultado de `SELECT COUNT(*) FROM admins;` (ou query equivalente) **ou** salvar log de `psql` com timestamp.

## Notas

- Este runbook não valida Lexiq, RAG nem PDF — apenas integridade de schema e presença de seeds acordados.
- Para ambiente **CI Playwright integrado**, use Postgres efêmero + `0005_ci_playwright_admin.sql` (usuário `ci-dashboard@qualidiagiq.test`).
