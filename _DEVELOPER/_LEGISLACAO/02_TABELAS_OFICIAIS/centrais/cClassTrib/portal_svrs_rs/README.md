# Portal SVRS-RS — Classificação Tributária (cClassTrib)

> Coleta da fonte autoritativa SEFAZ-RS para a tabela cClassTrib da Reforma Tributária.

## Origem

- **URL:** https://dfe-portal.svrs.rs.gov.br/CFF/ClassificacaoTributaria
- **Mantenedor:** Portal DF-e SEFAZ-RS (SVRS)
- **Data da extração:** 2026-04-26
- **Método:** Captura HTML + parsing do array JS embutido (`var dadosOriginais`)

## Arquivos

| Arquivo | Tamanho | Descrição |
|---|---|---|
| `cClassTrib_SVRS_RS_Reforma_Tributaria.xlsx` | 296 KB | Excel consolidado com 5 abas (Resumo, CST, cClassTrib, Anexos, Dicionário) |
| `cClassTrib_svrs_extracted.csv` | 104 KB | CSV flat denormalizado (156 linhas × 48 colunas) UTF-8 BOM |
| `cClassTrib_svrs_extracted.json` | 4,4 MB | JSON hierárquico completo com Anexos NCM/NBS aninhados |

## Conteúdo

| Métrica | Quantidade |
|---|---|
| CSTs (códigos pais) | **18** |
| cClassTrib (filhos) | **156** |
| Anexos NCM/NBS | **4.628** |
| Vigência inicial | 2025-05-01 |
| Vigência final | em aberto (todos ativos) |

## Estrutura do Excel

1. **00_Resumo** — Metadados, fonte oficial, distribuição de cClassTrib por CST com fórmulas de %
2. **01_CST** — 18 CSTs com 10 indicadores de regime (IndExigeTrib, IndMonofasica, IndReducaoAliq, etc.)
3. **02_cClassTrib** — 156 registros × 37 colunas, incluindo aplicabilidade nos 14 modelos de DF-e (NF-e, NFC-e, CT-e, BP-e, NF3e, NFCom, NFS-e etc.) + URL do artigo da LC 214/2025
4. **03_Anexos_NCM_NBS** — 4.628 itens NCM/NBS associados aos cClassTribs com permissão (PERMITIDO/VEDADO), condições e exceções
5. **04_Dicionario** — Dicionário de dados de todos os 56 campos com tipo, descrição e origem

## Próximos Passos Sugeridos (ADR-005)

1. **Diff vs versões anteriores** — comparar com `cClassTrib_v2026-04-15.xlsx` da pasta pai para detectar mudanças
2. **Ingestão Supabase** — gerar migration Postgres com tabelas `tributario.cst`, `tributario.cclasstrib`, `tributario.cclasstrib_anexo` (Clean Architecture / multi-tenant via RLS)
3. **Pipeline de extração contínua** — Edge Function agendada (semanal) com diff automático no GitHub
4. **Integração QFI / QDI** — uso na validação de fornecedores e classificação de operações
