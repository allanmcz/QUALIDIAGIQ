# WeasyPrint — runtime e limites (C4 / checklist PDF B.3)

Motor: `WeasyPrintPdfGenerator` (`src/infrastructure/adapters/pdf_generator_weasyprint.py`).

## Variáveis de ambiente

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `QDI_PDF_RENDER_TIMEOUT_SECONDS` | `90` | Timeout por geração (`asyncio.wait_for` em torno do render). |

## Container / SO

- **Fontes:** incluir pacotes de fontes no Dockerfile de deploy (ex.: `fonts-dejavu-core` ou equivalente) para evitar fallback inconsistente entre ambientes.
- **Locale:** `LANG`/`LC_ALL` UTF-8 recomendados para datas e textos PT-BR no template Jinja.
- **Memória:** relatórios muito grandes (dezenas de páginas) podem exigir limite de memória do pod/VM documentado na sua plataforma (Kubernetes `resources.limits.memory`, etc.).

## Homologação

- Itens **B.2** (sign-off contábil/produto) permanecem manuais (`docs/operacao/PDF_HOMOLOGACAO_CHECKLIST_B1.md`).
- **B.3** (técnico): timeout documentado aqui + checklist PDF atualizado no repositório.
