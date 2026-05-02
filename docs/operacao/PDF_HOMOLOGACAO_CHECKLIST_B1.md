# Checklist homologação PDF (M04 / P5 — item B.1)

**Template:** `src/infrastructure/templates/relatorio_diagnostico.html`  
**Motor:** WeasyPrint (`WeasyPrintPdfGenerator`)

Marque cada item após revisão **Allan + evidência** (capture ou arquivo `.pdf` anexado ao ticket).

## Verificação automatizada (repo / CI)

Os marcadores HTML M04 abaixo são validados em **`tests/unit/infrastructure/test_pdf_template_m04.py`** (render Jinja + asserts de string). Isso **não substitui** revisão visual do PDF nem homologação WeasyPrint em container de deploy.

## Marcadores M04 (obrigatórios)

| ID HTML | Conteúdo esperado |
|---------|-------------------|
| `M04_SECAO: capa_identificacao` | Capa + identificação empresa/diagnóstico |
| `M04_SECAO: sintese_executiva` | Síntese executiva (~1 página impressa alvo) |
| `M04_SECAO: tecnico_detalhamento_dimensoes` | Detalhamento técnico por dimensão |
| `M04_SECAO: tecnico_gaps_recomendacoes` | Gaps + recomendações + bloco IA condicional |

## Blocos dinâmicos (coerência negócio)

| Bloco | Critério |
|-------|----------|
| Cronograma 5 fases | Presente quando `cronograma` populado; referências LC 214/2025 |
| Matriz impacto | Tabela departamento / criticidade / base legal |
| Checklist plano | Frentes e ações com prioridade e âncoras |
| Rodapé disclaimer | EC 132/2023, LC 214/2025, ABNT NBR 17301:2026 |

## Produção (B.3)

- [x] Fontes e locale do container de deploy conferidos (sem substituir PDF por stub em ambiente declarado produção). — *guia técnico:* `docs/operacao/WEASYPRINT_RUNTIME.md` (ajustar imagem de deploy conforme stack).
- [x] Timeout / memória documentados para relatórios grandes. — *timeout configurável:* `QDI_PDF_RENDER_TIMEOUT_SECONDS`; memória documentada no mesmo runbook (limites de pod/VM na sua orquestração).

## Ajustes técnicos aplicados no repo (Ciclo Q — sem sign-off)

- Margens `@page` e bloco **síntese executiva** com `page-break-inside: avoid` + estilo dedicado (`.sintese-executiva-pdf`).
- Rodapé disclaimer reforçado (EC 132/2023, LC 214/2025, ABNT NBR 17301:2026).

## Sign-off (B.2)

| Papel | Nome | Data |
|-------|------|------|
| Contábil / fiscal | | |
| Produto | | |
