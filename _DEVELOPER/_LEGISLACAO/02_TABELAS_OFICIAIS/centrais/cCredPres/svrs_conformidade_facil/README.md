# 📥 SVRS Conformidade Fácil — Tabela de Crédito Presumido (cCredPres)

> Coleta da página **server-rendered** do Portal Conformidade Fácil da SVRS-RS, complementar aos arquivos XLSX oficiais do Portal NF-e.

**Fonte:** https://dfe-portal.svrs.rs.gov.br/CFF/TabelaCreditoPresumido
**Coletado em:** 2026-04-26
**Total de registros:** 13 códigos cCredPres

## Arquivos nesta pasta

| Arquivo | Descrição | Uso |
|---|---|---|
| `SVRS_TabelaCreditoPresumido_2026-04-26.html` | HTML bruto original | Auditoria/prova documental |
| `SVRS_cCredPres_estruturado.json` | JSON aninhado com vigência IBS/CBS por código | APIs, agentes LangChain |
| `SVRS_cCredPres_achatado_por_tributo.csv` | CSV achatado (1 linha por código × tributo) | Ingestão Supabase com FK por tributo |
| `SVRS_cCredPres_simples.csv` | CSV simples (1 linha por código, colunas IBS_*/CBS_*) | Pivot/Excel/análise rápida |

## Schema do JSON

```json
{
  "_numero_secao": 1,
  "Código": "1",
  "Descrição": "Crédito presumido da aquisição de bens e serviços de produtor rural...",
  "Apropria DFE": "Sim",
  "Apropria Evento": "Sim",
  "Deduz Crédito Presumido": "Não",
  "Vigência por Tributo": {
    "IBS": { "Aplicável": "Sim", "Início Vigência": "01/01/2027", "Fim Vigência": "Indeterminado" },
    "CBS": { "Aplicável": "Sim", "Início Vigência": "01/01/2027", "Fim Vigência": "Indeterminado" }
  }
}
```

## Diferença vs. XLSX do Portal NF-e

| Aspecto | XLSX (Portal NF-e) | HTML (SVRS Conformidade Fácil) |
|---|---|---|
| Granularidade temporal | snapshot da publicação | renderizado em tempo real |
| Estrutura | tabular flat | aninhada por tributo (IBS/CBS) |
| Campos extras | indicadores técnicos NF-e | vigência por tributo, "Apropria DFE/Evento" |
| Útil para | ingestão massiva inicial | validação cruzada / fluxo de aplicação |

> **Recomendação técnica:** use o XLSX como **fonte da verdade estrutural** e o HTML SVRS como **validação cruzada** (especialmente para datas de início/fim de vigência por tributo).

## Outras páginas SVRS relacionadas (não baixadas — sugestão futura)

- https://dfe-portal.svrs.rs.gov.br/CFF/ClassificacaoTributaria — tabela cClassTrib navegável
- https://dfe-portal.svrs.rs.gov.br/CFF/ClassificacaoTributariaNCM — cClassTrib × NCM
- https://dfe-portal.svrs.rs.gov.br/CFF/ValidadorRTC — validador online de DF-e RTC
- https://dfe-portal.svrs.rs.gov.br/CFF/Servicos — autenticação por certificado digital para serviços avançados
