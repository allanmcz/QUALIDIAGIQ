# ADR-013 — Convenção de sufixo `a/b/c` em migrações SQL com o mesmo número

| Campo | Valor |
|-------|--------|
| **Status** | Aceita |
| **Data** | 2026-05-10 |
| **Contexto** | Duas migrações com prefixo `0005_*` geravam ordem lexical implícita pelo segundo segmento do nome de ficheiro, frágil em `ls \| sort` e em revisões. |
| **Decisão** | Quando duas ou mais migrações partilham o mesmo número de sequência no mesmo dia (ou ramos paralelos), usar sufixo alfabético: `0005a_*`, `0005b_*`, etc., preservando ordem lexical explícita. |
| **Alternativas** | Renumerar toda a cadeia (`0006`, `0007`…) — rejeitada por conflitos com histórico já aplicado em ambientes. Prefixo timestamp — rejeitada por quebrar convenção atual `NNNN_*.sql`. |
| **Consequências** | Nomes mais longos; ordem de aplicação óbvia em CI e `init.sql`. |
