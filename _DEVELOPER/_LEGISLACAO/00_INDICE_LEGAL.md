# Índice Legal — Base Normativa Tributiq Onda 1.0

> **Esta pasta concentra TODA a base legal necessária** para construir, defender e operar os 3 produtos da Onda 1.0. É a fonte canônica usada pela Lexiq RAG.

---

## 1. Estrutura

```
03_LEGISLACAO/
├── 00_INDICE_LEGAL.md              ← este arquivo
├── 01_REFORMA_TRIBUTARIA/          ← Reforma Tributária do Consumo
│   ├── EC_132_2023/                ← Emenda Constitucional 132/2023
│   ├── LC_214_2025/                ← Lei Complementar 214/2025
│   ├── LC_227_2026/                ← Lei Complementar 227/2026 (CGIBS)
│   ├── ATOS_CONJUNTOS/             ← Atos Conjuntos RFB/CGIBS
│   ├── RESOLUCOES_SENADO/          ← Resoluções fixando alíquotas referência
│   └── demais_normas/              ← portarias, decretos relacionados
├── 02_TABELAS_OFICIAIS/
│   ├── normalizado/csv/            ← cClassTrib, cCredPres, CST, NCM em CSV
│   ├── normalizado/json/           ← idem em JSON
│   ├── centrais/                   ← brutos cClassTrib, cCredPres, CST_CBS_IBS
│   └── auxiliares/                 ← NCM, CFOP, GTIN, cBenef, cIndBiocomb
├── 03_NORMAS_TECNICAS/
│   ├── NT_2025-002_*.pdf           ← versões 1.00 → 1.33
│   ├── RT_NT_2024-002_*.pdf        ← Regulamento Técnico
│   ├── IT_v1.31_v1.40_v1.50/       ← Informes Técnicos (a coletar)
│   ├── MOC_v7.0/                   ← Manual Orientação Contribuinte (a coletar)
│   └── schemas_xsd/                ← Schemas XSD NF-e RTC
├── 04_LEGISLACAO_TRANSVERSAL/
│   ├── LGPD/                       ← Lei 13.709/2018
│   ├── MARCO_CIVIL_INTERNET/       ← Lei 12.965/2014
│   ├── LEI_DO_SOFTWARE/            ← Lei 9.609/1998
│   └── CODIGO_CIVIL/               ← Lei 10.406/2002 (contratos)
├── 05_PARECERES_INTERNOS/
│   ├── PT-001 a PT-011             ← 11 pareceres técnicos do projeto
│   ├── PT-API-001                  ← Parecer API Oficial CBS/IBS
│   └── (a expandir)
└── 06_CALCULADORA_RFB/
    ├── spec_oficial/               ← OpenAPI 3.1 + 27 endpoints
    └── guia_integracao/            ← scripts Python de integração
```

## 2. Documentos canônicos por categoria

### 🏛️ Reforma Tributária (essenciais)

| Documento | Vigência | Localização |
|-----------|----------|-------------|
| EC nº 132/2023 | 20/12/2023 | `01_REFORMA_TRIBUTARIA/EC_132_2023/` |
| LC nº 214/2025 | 16/01/2025 | `01_REFORMA_TRIBUTARIA/LC_214_2025/` |
| LC nº 227/2026 (CGIBS) | 13/01/2026 | `01_REFORMA_TRIBUTARIA/LC_227_2026/` (a baixar) |
| Ato Conjunto RFB/CGIBS nº 1/2025 | 2025 | `01_REFORMA_TRIBUTARIA/ATOS_CONJUNTOS/` (a baixar) |

### 📊 Tabelas oficiais (1.890 registros normalizados)

| Tabela | Vigência | Versões |
|--------|----------|---------|
| cClassTrib | 2026-04-15 | 9 versões (2024-12 → 2026-04-15) |
| cCredPres | 2025-12-15 | 4 versões |
| CST IBS/CBS | 2025-05-19 | 1 versão |
| NCM | 2026-02-01 | vigente |
| CFOP | 2023-04-24 | vigente |
| GTIN/GS1 | atual | prefixos |
| cBenef×CST | 2019.001 | PR/RJ/RS |
| cIndBiocomb | atual | — |

### 📋 Normas técnicas

| Norma | Versão | Status |
|-------|--------|:--:|
| NT 2025.002 | v1.00 → v1.33 (atual) | ✅ |
| RT NT 2024.002 | v1.10 | ✅ |
| Informe Técnico | v1.31 / v1.40 / v1.50 | 🟡 a verificar |
| MOC | v7.0 + Anexo I | 🟡 a verificar |
| Schemas XSD NF-e RTC | NT 2025.002 v1.30 | ✅ |
| Schemas XSD PL010c | NT 2022.002 | ✅ |

### ⚖️ Legislação transversal (LGPD, etc.)

| Norma | Aplicação no Tributiq |
|-------|------------------------|
| LGPD (Lei 13.709/2018) | Termo de consentimento + DPA + criptografia + RLS |
| Marco Civil da Internet (Lei 12.965/2014) | Termos de uso + logs + neutralidade |
| Lei do Software (Lei 9.609/1998) | Direitos autorais sobre código Tributiq |
| Código Civil (Lei 10.406/2002) | Contratos B2B com clientes Tributiq |

## 3. Pareceres internos PT-001 a PT-011

Todos em `05_PARECERES_INTERNOS/`:

| ID | Tema |
|----|------|
| PT-001 | Visão Geral Classificação Reforma |
| PT-002 | cClassTrib NT 2025.002 |
| PT-003 | NCM Classificação Mercantil |
| PT-004 | CST PIS/COFINS vs CBS/IBS |
| PT-005 | Regimes Específicos e Diferenciados |
| PT-006 | Alíquotas e Reduções |
| PT-007 | Cesta Básica Nacional Alíquota Zero |
| PT-008 | Imposto Seletivo Classificação |
| PT-009 | Crédito Presumido Não-Cumulatividade |
| PT-010 | Operações Especiais ZFM e Devoluções |
| PT-011 | Serviços e Operações Híbridas |
| PT-API-001 | API Oficial CBS/IBS (RFB) |

## 4. Hierarquia normativa (ordem de aplicação)

Quando classificar/decidir, **sempre** consultar nesta ordem:

1. **Constituição Federal** (especialmente art. 156-A com redação dada pela EC 132)
2. **EC nº 132/2023**
3. **LC nº 214/2025** (regulamentação principal)
4. **LC nº 227/2026** (CGIBS)
5. **Resoluções do Senado Federal** (alíquotas referência)
6. **Notas Técnicas RFB/CGIBS** (NT 2025.002)
7. **Atos Conjuntos RFB/CGIBS**
8. **Informes Técnicos (IT)**
9. **Manual de Orientação ao Contribuinte (MOC)**
10. **Tabelas oficiais** (cClassTrib, cCredPres, CST)
11. **Pareceres técnicos internos** (PT-001 a PT-011)
12. **Jurisprudência** (STF/STJ/CARF — quando houver)

## 5. Arquivos a baixar/coletar

🟡 **Pendentes para Sprint S1** (priorizar):

- [ ] LC nº 227/2026 (PLP 108/2024) — texto completo Planalto
- [ ] Ato Conjunto RFB/CGIBS nº 1/2025 — diário oficial
- [ ] Informe Técnico v1.31, v1.40 e v1.50 (Portal NF-e)
- [ ] MOC v7.0 + Anexo I (Portal NF-e)
- [ ] LGPD texto integral (Planalto) — para compliance
- [ ] Marco Civil da Internet — texto integral
- [ ] Lei do Software 9.609/1998 — texto integral
- [ ] Código Civil — capítulo de contratos digitais

## 6. Regras de uso da base legal pela Lexiq

### Versionamento

Toda regra/citação deve carregar:
- `vigencia_inicio` (date NOT NULL)
- `vigencia_fim` (date NULL para vigente)
- `fonte` (texto: ex: "LC 214/2025, art. 8º")
- `hash_sha256` do chunk

### Re-snapshot mensal

Worker Dagster (sensor) executa todo dia 01 de cada mês:
1. Verifica se há nova versão da NT 2025.002 no Portal NF-e.
2. Verifica novas Resoluções do Senado.
3. Verifica novos Atos Conjuntos RFB/CGIBS.
4. Re-indexa Lexiq se houver delta.
5. Notifica Slack se mudanças impactarem clientes.

### Fallback offline

Componente offline RFB (`.jar` ~254 MB) preserva snapshot de **2025-12** como base de continuidade absoluta em caso de outage da API ou bloqueio de porta 18016.

## 7. Política de citação obrigatória

Toda decisão fiscal sugerida pela IA do Tributiq **deve** carregar:
- ✅ Artigo + parágrafo da norma fonte
- ✅ Anexo (se aplicável)
- ✅ Vigência aplicada
- ✅ Score de confiança do retriever
- ✅ Hash do chunk

Sem isso → HTTP 422 (Unprocessable Entity).

## 8. Decisões a documentar via ADR

| Decisão | ADR sugerida |
|---------|--------------|
| Build vs. Buy do motor de cálculo | ADR-009 (a redigir) |
| Estratégia de fallback bloqueio porta 18016 | ADR-002-QMI ✅ |
| Versionamento normativo Lexiq | ADR-010 (a redigir) |
| WORM com S3 Object Lock | ADR-011 (a redigir) |
| Multi-tenant RLS Supabase | ADR-001-QMI ✅ |

---

**Última atualização:** 2026-04-29 · revisar quinzenalmente.
