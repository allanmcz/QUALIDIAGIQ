# Homologação PDF — marcadores M04 (QDI)

> Base: MUST **M04** — gaps/recomendações técnicas no relatório.  
> **P5 fatia (2026-05-01):** evidência **automatizada** via `tests/unit/infrastructure/test_pdf_template_m04.py` (HTML Jinja antes do WeasyPrint).

## Evidência automatizada (CI)

| Critério | OK | Fonte |
|----------|---:|--------|
| Marcador `M04_SECAO: tecnico_gaps_recomendacoes` no HTML | **Sim** | `test_template_relatorio_contem_secoes_m04_e_normativo` |
| Seções `capa_identificacao`, `sintese_executiva` | **Sim** | idem |
| Textos visíveis: “Síntese executiva”, “Cronograma em cinco horizontes”, “Base legal (referência)”, “Matriz de impacto por departamento” | **Sim** | idem |

## Homologação manual (staging/prod — Allan)

| Critério | OK | Observação |
|----------|---:|------------|
| PDF binário abre sem erro (Acrobat/browser) | ☐ | Após `gerar_pdf` real |
| Renderização WeasyPrint idêntica ao HTML esperado (fontes, quebras) | ☐ | |
| Rodapé / versão normativa legível | ☐ | |
| Dados conferidos com GET `/diagnosticos/{id}` | ☐ | |

**Próximo passo:** gerar PDF pelo fluxo da API em Docker (`make dev`) + marcar linhas manuais acima.
