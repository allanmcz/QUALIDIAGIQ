# 03 — Exemplos de Payload Anotados

> Os arquivos JSON estão em [`examples/`](../examples/). Aqui temos a explicação de cada um, incluindo a **lógica tributária subjacente** ao payload.

---

## 1. `regime-geral.json` — Cálculo Completo (CBS + IBS + IS)

**Endpoint:** `POST /calculadora/regime-geral`
**Cenário:** Operação mista — uma venda de cigarros (NCM 2402.10.00, sujeito a Imposto Seletivo) + uma prestação de serviço (NBS 1.0905.21.00).

```json
{
  "id": "6194602ea71cbf9431c236de4409d920",
  "versao": "0.0.1",
  "dhFatoGerador": "2026-03-15T14:30:00-03:00",
  "municipio": 4314902,
  "uf": "RS",
  "itens": [
    {
      "numero": 1,
      "ncm": "24021000",
      "cst": "000",
      "cClassTrib": "000001",
      "baseCalculo": 200.00,
      "quantidade": 10,
      "unidade": "UN",
      "tributacaoRegular": { "cst": "000", "cClassTrib": "000001" },
      "impostoSeletivo": {
        "cst": "000",
        "cClassTrib": "000002",
        "baseCalculo": 200.00,
        "quantidade": 10,
        "unidade": "UN",
        "impostoInformado": 12.00
      }
    },
    {
      "numero": 2,
      "nbs": "109052100",
      "cst": "000",
      "cClassTrib": "000001",
      "baseCalculo": 500.00,
      "quantidade": 1,
      "unidade": "SV",
      "tributacaoRegular": { "cst": "000", "cClassTrib": "000001" }
    }
  ]
}
```

**Pontos-chave:**
- O item 1 tem **dois blocos de tributação**: `tributacaoRegular` (CBS+IBS) E `impostoSeletivo` (IS — característica de produtos sujeitos ao IS, ex: cigarros, bebidas alcoólicas).
- O item 2 é um serviço (`nbs` em vez de `ncm`) sem IS.
- `dhFatoGerador` define a vigência das alíquotas (em 2026 vale a alíquota-teste).
- O município `4314902` (Porto Alegre) determina o `IBS-Mun`.

**Resposta esperada (resumida):**
```json
{
  "objetos": [
    {
      "tributos": {
        "IBSCBS": {
          "CST": "000", "cClassTrib": "000001",
          "gIBSCBS": {
            "vBC": 200.00,
            "gIBSUF": { "vIBSUF": 0.10, "pIBSUF": 0.05 },
            "gIBSMun": { "vIBSMun": 0.10, "pIBSMun": 0.05 },
            "vIBS": 0.20,
            "gCBS": { "vCBS": 1.80, "pCBS": 0.90 }
          }
        },
        "ImpostoSeletivo": {
          "CSTIS": "000", "cClassTribIS": "000002",
          "vBCIS": 200.00, "vIS": 12.00,
          "memoriaCalculo": "..."
        }
      }
    },
    {  /* item 2 — apenas IBS+CBS */ }
  ],
  "total": {
    "tributos": {
      "gIBSCBSTot": { "vIBSTot": 0.70, "vCBSTot": 6.30 },
      "gISTot": { "vISTot": 12.00 }
    }
  }
}
```

---

## 2. `base-calculo-cibs.json` — BC Isolada do CIBS

**Endpoint:** `POST /calculadora/base-calculo/cbs-ibs-mercadorias`
**Cenário:** Calcular apenas a BC do CIBS para uma venda de R$ 1.000,00 com ICMS, PIS e COFINS embutidos (cenário 2026 — período de transição).

```json
{
  "anoFatoGerador": 2026,
  "valorBem": 1000.00,
  "frete": 50.00,
  "icms": 180.00,
  "pis": 16.50,
  "cofins": 76.00,
  "descontoIncondicional": 100.00
}
```

**Lógica subjacente (LC 214/2025, arts. 12 e 13):**
> A BC do CIBS = Valor da operação **+** acréscimos **−** descontos incondicionais **−** tributos a serem extintos (ICMS, PIS, COFINS, IPI quando aplicável).

**Resposta esperada:**
```json
{ "baseCalculo": 677.50 }
```
(`1000 + 50 - 100 - 180 - 16.50 - 76 = 677.50`)

> ⚠️ **Atenção:** Em 2027 não envie mais `pis`/`cofins` (extintos); em 2033 não envie `icms`/`iss`. A API retornará erro 400.

---

## 3. `base-calculo-is.json` — BC Isolada do IS

**Endpoint:** `POST /calculadora/base-calculo/is-mercadorias`
**Cenário:** BC do IS em 2027 (após extinção PIS/COFINS).

```json
{
  "anoFatoGerador": 2027,
  "valorBem": 1000.00,
  "freteCobrado": 50.00,
  "icms": 180.00,
  "descontoIncondicional": 0.00,
  "bonificacao": 0.00,
  "devolucaoVendas": 0.00
}
```

> 💡 **Diferença vs CIBS:** Aqui não há `pis`, `cofins`, `pisImportacao`, `cofinsImportacao` (o IS não os deduz). Mas aceita `bonificacao` (art. 417 §2º) e `devolucaoVendas` (art. 418).

---

## 4. `nfse-base-calculo.json` — BC de NFS-e

**Endpoint:** `POST /calculadora/nfse/base-calculo`
**Cenário:** Prestação de serviço de R$ 5.000,00 com ISS, PIS e COFINS atuais.

```json
{
  "anoFatoGerador": 2026,
  "valorServico": 5000.00,
  "descontoIncondicional": 100.00,
  "iss": 250.00,
  "pis": 32.50,
  "cofins": 150.00
}
```

**Campos especiais para serviços específicos:**
- `vCalcReeRepRes` — valor de reembolso/repasse/ressarcimento de bens fornecidos por terceiros (não compõe BC do ISS/IBS/CBS — útil para consultorias com despesas reembolsáveis).
- `vCalcDedRedIBSCBS` — deduções/reduções para **locação de imóveis, cessão onerosa, arrendamento, serviços médicos** (art. 6º LC 214/2025).

---

## 5. `pedagio.json` — IVA-Pedágio (NFS-e Via)

**Endpoint:** `POST /calculadora/pedagio`
**Cenário:** Concessionária de pedágio com 3 trechos em RS, SC e PR, totalizando 250,8 km.

```json
{
  "dataHoraEmissao": "2027-01-15T08:00:00-03:00",
  "codigoMunicipioOrigem": 4314902,
  "ufMunicipioOrigem": "RS",
  "cst": "000",
  "cClassTrib": "000002",
  "baseCalculo": 250.00,
  "trechos": [
    { "numero": 1, "municipio": 4314902, "uf": "RS", "extensao": 50.5 },
    { "numero": 2, "municipio": 4202404, "uf": "SC", "extensao": 120.0 },
    { "numero": 3, "municipio": 4106902, "uf": "PR", "extensao": 80.3 }
  ]
}
```

**Lógica:** A API distribui proporcionalmente a BC entre os municípios atravessados (regra de rateio do IBS-Mun para serviços de transporte/pedágio — art. 11 LC 214/2025).

---

## 6. Validação de XML

**Endpoint:** `POST /calculadora/xml/validate?tipo=nfe&subtipo=nota`

```bash
curl -X POST \
  "https://consumo.tributos.gov.br:18016/servico/calcular-tributos-consumo/api/calculadora/xml/validate?tipo=nfe&subtipo=nota" \
  -H "Content-Type: application/xml" \
  --data-binary @minha_nfe.xml
```

> **Use case Tributiq:** integrar no QualiFiscaIQ como **pré-validação** antes do envio à SEFAZ-RS — economiza um round-trip ao webservice oficial.

---

## 7. Geração de XML a partir do ROC

**Endpoint:** `POST /calculadora/xml/generate?tipo=nfe`
**Body:** o `ROCDomain` retornado pelo `/regime-geral`.

Fluxo completo:
```
[OperacaoInput] → POST /regime-geral → [ROCDomain]
                                          ↓
                                    POST /xml/generate?tipo=nfe
                                          ↓
                                    [XML pronto p/ assinar e transmitir]
```

---

## 8. Health Check

```bash
curl -s "https://consumo.tributos.gov.br:18016/servico/calcular-tributos-consumo/api/calculadora/dados-abertos/versao"
```

```json
{
  "versaoApp": "0.0.0-SNAPSHOT",
  "versaoDb": "1.0.0",
  "descricaoVersaoDb": "Versão de homologação",
  "dataVersaoDb": "2026-01-01",
  "ambiente": "Online"
}
```

> **Padrão sugerido para Tributiq:** monitor Prometheus que faz ping nesse endpoint a cada 60s e dispara alerta se `versaoDb` mudar (sinal de que tabelas foram atualizadas e cache local precisa ser invalidado).
