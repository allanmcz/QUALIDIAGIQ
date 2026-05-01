# 📊 CALCULAR_TRIB_REFORMA — Calculadora Oficial de Tributos do Consumo (Reforma Tributária)

> **Espelho técnico-arquitetural** da API oficial da Receita Federal/Serpro para cálculo de **CBS, IBS e Imposto Seletivo (IS)** no contexto da **Reforma Tributária do Consumo (LC 214/2025 + EC 132/2023)**, voltado para integração no ecossistema **Tributiq**.
>
> **Coletado em:** 26/04/2026 · **Fonte oficial:** `https://consumo.tributos.gov.br` · **Versão da spec:** OpenAPI 3.1.0 · **Status:** VERSÃO BETA

---

## 🎯 Resumo Executivo (TL;DR para o Arquiteto)

A **Calculadora de Tributos do Consumo** é o **motor de cálculo oficial da RFB** ("conteúdo normativo embarcado") para a Reforma Tributária. Funciona em três modalidades:

| Modalidade | Endpoint base | Uso recomendado |
|---|---|---|
| **Online (REST)** | `https://consumo.tributos.gov.br:18016/servico/calcular-tributos-consumo/api` | MVPs, simulações ad-hoc, integrações leves |
| **Offline (componente)** | Download em `piloto-cbs.tributos.gov.br/.../calculadora-offline` | ERPs/sistemas com volume alto, sigilo e autonomia técnica |
| **Assistente de Emissão** | Embarcado | Geração automática dos grupos CBS/IBS/IS no XML do DF-e |

**Modelo conceitual:** Tax-as-a-Service (TaaS) público, alinhado à **Administração Tributária 3.0 da OCDE**. Pode rodar **sem conexão com a RFB** (via componente local).

A API expõe **27 endpoints** distribuídos em **5 grupos** (Calculadora, Base de Cálculo, NFS-e, Pedágio e Dados Abertos), todos em **VERSÃO BETA**.

---

## 🧭 Como Navegar Esta Pasta

```
CALCULAR_TRIB_REFORMA/
├── README.md                          ← você está aqui
├── raw/                               ← arquivos brutos da API
│   ├── openapi.json                   ← spec OpenAPI 3.1.0 (porta 18016)
│   ├── openapi-v3.json                ← spec OpenAPI 3.1.0 (porta 18018)
│   ├── swagger-config.json            ← config do Swagger UI
│   ├── swagger-ui.html                ← shell HTML
│   └── swagger-initializer.js         ← init JS
├── docs/
│   ├── 00-visao-geral.md              ← contexto da Reforma + arquitetura
│   ├── 01-endpoints.md                ← referência completa dos 27 endpoints
│   ├── 02-schemas.md                  ← 63 schemas (DTOs) catalogados
│   ├── 03-exemplos-payload.md         ← payloads JSON anotados
│   ├── 04-integracao-tributiq.md      ← arquitetura Clean Architecture p/ Tributiq
│   └── 05-referencias.md              ← links oficiais, NTs, manuais
├── examples/
│   ├── regime-geral.json              ← cálculo CBS/IBS/IS regime geral
│   ├── nfse-base-calculo.json         ← base de cálculo de NFS-e
│   ├── pedagio.json                   ← cálculo IVA-Pedágio
│   ├── base-calculo-cibs.json         ← base CIBS isolada
│   └── base-calculo-is.json           ← base do Imposto Seletivo isolada
└── clients/
    ├── python/                        ← cliente httpx + Pydantic
    │   └── calculadora_client.py
    └── typescript/                    ← cliente Fetch + Zod
        └── calculadora-client.ts
```

---

## 🚀 Quickstart (5 minutos)

### 1️⃣ Verificar versão (sem auth, ping de saúde)

```bash
curl -s "https://consumo.tributos.gov.br:18016/servico/calcular-tributos-consumo/api/calculadora/dados-abertos/versao" | jq
```

Resposta esperada:
```json
{
  "versaoApp": "0.0.0-SNAPSHOT",
  "versaoDb": "1.0.0",
  "descricaoVersaoDb": "Versão de homologação",
  "dataVersaoDb": "2026-01-01",
  "ambiente": "Online"
}
```

### 2️⃣ Calcular tributos (Regime Geral)

```bash
curl -s -X POST \
  "https://consumo.tributos.gov.br:18016/servico/calcular-tributos-consumo/api/calculadora/regime-geral" \
  -H "Content-Type: application/json" \
  -d @examples/regime-geral.json | jq
```

### 3️⃣ Cliente Python (Tributiq)

```python
from clients.python.calculadora_client import CalculadoraClient

cli = CalculadoraClient()
versao = cli.consultar_versao()
print(versao.versao_app, versao.ambiente)
```

---

## 📌 Pontos de Atenção do Arquiteto

| # | Tópico | Risco / Decisão |
|---|---|---|
| 1 | **Toda API está em BETA** | Contrato pode mudar; encapsule em **adapter/gateway** (Hexagonal) para isolar o domínio Tributiq de breaking changes. |
| 2 | **Sem versionamento explícito de URL** (`/v1/`, `/v2/`) | Use o endpoint `/dados-abertos/versao` para detectar mudanças e disparar testes de regressão. |
| 3 | **Campo `dataHoraEmissao` será descontinuado** em `OperacaoInput` | Migrar para `dhFatoGerador` desde já — está documentado no próprio schema. |
| 4 | **Endpoint `classificacoes-tributarias/{idSituacaoTributaria}` está DEPRECATED** | Use as variantes `/cbs-ibs/{cst}` ou `/imposto-seletivo/{cst}`. |
| 5 | **Alíquotas-teste 2026** (CBS 0,9% / IBS 0,1%) | A API retorna a alíquota vigente conforme `data` (ISO 8601); cache deve respeitar TTL diário. |
| 6 | **Servidor responde na porta 18016** (não na 443) | Atenção a firewalls corporativos / proxies — abrir egress para porta custom. |
| 7 | **Resposta 422 para validação** | Use `ProblemDetail` (RFC 7807) para mapeamento padronizado de erros. |
| 8 | **Dados Abertos exigem `data` (ISO 8601)** em quase todos os GETs | Permite consulta histórica — ideal para reprocessamento de períodos anteriores. |

---

## 🔗 Próximos Passos Sugeridos (no projeto Tributiq)

1. **Criar adapter `02_products/qualifiscaIQ/src/infrastructure/calculadora_rfb/`** com Clean Architecture (porta `domain/ports/calculadora_port.py` → adapter `infrastructure/calculadora_rfb/client.py`).
2. **Materializar tabelas auxiliares** no Supabase (`tab_cclass_trib`, `tab_cst_cbs_ibs`, `tab_aliquotas_uf_mun`) a partir dos endpoints `/dados-abertos/*` em job noturno (Edge Function + cron).
3. **Implementar Circuit Breaker** (ex.: `tenacity` no Python, `cockatiel` no TS) — RFB já avisa que pode haver instabilidade no Beta.
4. **Cache distribuído (Redis)** das respostas de Dados Abertos com TTL de 24h, chave `{endpoint}:{data_iso}`.
5. **Testes de contrato (Pact ou snapshot)** validando o OpenAPI contra a versão local — alerta automático em CI quando a RFB alterar o contrato.

---

## 📚 Documentação Oficial e Referências

Veja [`docs/05-referencias.md`](docs/05-referencias.md) para a lista completa. Principais:

- **Portal oficial:** https://consumo.tributos.gov.br
- **Swagger UI ao vivo:** https://consumo.tributos.gov.br/servico/calcular-tributos-consumo/api/swagger-ui/index.html
- **Manual RTC v1 (PDF):** https://www.gov.br/receitafederal/pt-br/centrais-de-conteudo/publicacoes/manuais/reforma-tributaria-do-consumo/manual-servicos-rtc.pdf
- **Comunicado Beta Produção (dez/2025):** https://www.gov.br/receitafederal/pt-br/centrais-de-conteudo/publicacoes/manuais/reforma-tributaria-do-consumo/comunicado-sobre-o-ambiente-de-producao-beta-versao-1-dezembro25
- **Notícia oficial de lançamento (jul/2025):** https://www.gov.br/receitafederal/pt-br/assuntos/noticias/2025/julho/receita-federal-libera-ferramenta-oficial-de-calculo-da-reforma-tributaria-sobre-o-consumo
- **Orientações 2026:** https://www.gov.br/receitafederal/pt-br/acesso-a-informacao/acoes-e-programas/programas-e-atividades/reforma-consumo/orientacoes-2026
- **CGIBS — Comitê Gestor do IBS:** https://www.cgibs.gov.br
- **LC 214/2025:** http://www.planalto.gov.br/ccivil_03/leis/lcp/lcp214.htm
- **EC 132/2023:** https://www.planalto.gov.br/ccivil_03/constituicao/emendas/emc/emc132.htm

---

> Documento gerado pelo agente arquiteto Tributiq · Versão 1.0 · 26/04/2026
