# 01 — Referência Completa de Endpoints

> **Base URL:** `https://consumo.tributos.gov.br:18016/servico/calcular-tributos-consumo/api`
> **OpenAPI:** 3.1.0 · **Total de endpoints:** 27 · **Status:** VERSÃO BETA

Sumário rápido por grupo:

| Grupo (Tag) | Qtd | Função |
|---|---:|---|
| Calculadora | 5 | Cálculo principal CBS/IBS/IS + validação/geração de XML |
| Base de Cálculo | 2 | Cálculo isolado da BC (CIBS e IS) |
| NFS-e | 1 | Cálculo de BC específico de NFS-e |
| Pedágio | 1 | Cálculo IVA-Pedágio (NFS-e Via) |
| Dados Abertos | 17 | Tabelas auxiliares (UFs, NCM, NBS, CST, cClassTrib, alíquotas, fundamentação legal) |

Códigos de resposta padrão (todos os endpoints):
- **200** — Sucesso (Content-Type varia: `application/json` ou `application/xml`)
- **400** — Estrutura/dados em formato não reconhecido
- **404** — Erro na URL da requisição
- **422** — Erro de validação semântica
- **500** — Erro interno (`application/problem+json` — RFC 7807)

---

## 🟦 Grupo 1 — Calculadora (Cálculo principal)

### 1.1 `POST /calculadora/regime-geral`
> **operationId:** `calcularTributos` · **Coração da API**

**Descrição:** Recebe uma operação (lista de itens) e retorna o **ROC — Recibo da Operação de Consumo** com todos os tributos calculados (CBS, IBS-UF, IBS-Município, IS, monofasia, créditos presumidos, transferência de crédito, ajuste de competência etc.).

**Request:** `application/json` → [`OperacaoInput`](02-schemas.md#operacaoinput)
**Response 200:** `application/json` → [`ROCDomain`](02-schemas.md#rocdomain)

**Campos obrigatórios:** `id`, `versao`, `municipio`, `itens[]`

```bash
curl -X POST \
  "https://consumo.tributos.gov.br:18016/servico/calcular-tributos-consumo/api/calculadora/regime-geral" \
  -H "Content-Type: application/json" \
  -d @examples/regime-geral.json
```

---

### 1.2 `POST /calculadora/xml/validate`
> **operationId:** `validate`

**Descrição:** Valida a estrutura e os grupos CBS/IBS/IS de um XML de DF-e.

**Query params (obrigatórios):**
- `tipo`: `nfe | nfce | nfse | cte | cte-simplificado | bpe | bpe-tm | nf3e`
- `subtipo`: `grupo | nota` (valida apenas o grupo de tributação CBS/IBS ou a nota inteira)

**Request:** `application/xml` → corpo XML do DF-e
**Response 200:** `application/json` → relatório de validação

```bash
curl -X POST \
  "https://consumo.tributos.gov.br:18016/servico/calcular-tributos-consumo/api/calculadora/xml/validate?tipo=nfe&subtipo=nota" \
  -H "Content-Type: application/xml" \
  --data-binary @minha_nfe.xml
```

### 1.3 `GET /calculadora/xml/validate`
> **operationId:** `getDocumentosValidacao`

**Descrição:** Lista os tipos de DFe suportados pela validação.
**Response 200:** `application/json` → [`TipoDocumentoDTO`](02-schemas.md#tipodocumentodto)

---

### 1.4 `POST /calculadora/xml/generate`
> **operationId:** `generate`

**Descrição:** Gera o XML do DF-e a partir do **ROC** retornado pelo `/regime-geral` (caminho ROC → XML).

**Query params:** `tipo` (mesmos valores acima)
**Request:** `application/json` → [`ROCDomain`](02-schemas.md#rocdomain)
**Response 200:** `application/xml` → XML do DF-e

### 1.5 `GET /calculadora/xml/generate`
> **operationId:** `getDocumentosGeracao`

Lista os tipos de DFe suportados pela geração.

---

## 🟦 Grupo 2 — Base de Cálculo

### 2.1 `POST /calculadora/base-calculo/cbs-ibs-mercadorias`
> **operationId:** `calcularCibs` · **summary:** "CIBS"

**Descrição:** Calcula a **Base de Cálculo do CIBS (CBS + IBS) para mercadorias**, considerando ajustes (acréscimos, juros, multas, encargos, frete, IS, outros tributos, ICMS, ISS, PIS, COFINS, IPI, COSIP, descontos incondicionais).

**Request:** `application/json` → [`BaseCalculoCibsInput`](02-schemas.md#basecalculocibsinput)
**Response 200:** [`BaseCalculoISMercadoriasModel`](02-schemas.md#basecalculoismercadoriasmodel) — apenas `{baseCalculo: number}`

**Campos obrigatórios:** `anoFatoGerador` (int)

> ⚠️ **Erro 400:** retornado se enviar campos incompatíveis com o ano (ex: PIS/COFINS após 2027; ICMS/ISS após 2033).

---

### 2.2 `POST /calculadora/base-calculo/is-mercadorias`
> **operationId:** `calcularISMercadorias` · **summary:** "Imposto Seletivo"

**Descrição:** Calcula a **BC do Imposto Seletivo** para mercadorias. Diferenças vs CIBS: aceita `bonificacao` e `devolucaoVendas`, não aceita PIS/COFINS/CBS/IBS (são excluídos da própria BC do IS).

**Request:** [`BaseCalculoISMercadoriasInput`](02-schemas.md#basecalculoismercadoriasinput)
**Response 200:** [`BaseCalculoISMercadoriasModel`](02-schemas.md#basecalculoismercadoriasmodel)

> ⚠️ **Erro 400:** ICMS/ISS após 2033 (depois da extinção total).

---

## 🟦 Grupo 3 — NFS-e

### 3.1 `POST /calculadora/nfse/base-calculo`
> **operationId:** `calcularBaseCalculo` · **summary:** "Base de Cálculo NFS-e"

**Descrição:** Calcula a BC para NFS-e considerando deduções específicas (`vCalcReeRepRes`, `vCalcDedRedIBSCBS`).

**Request:** [`NfseBaseCalculoInput`](02-schemas.md#nfsebasecalculoinput)
**Response 200:** [`NfseBaseCalculoOutput`](02-schemas.md#nfsebasecalculooutput) → `{baseCalculo: number}`

**Campos obrigatórios:** `anoFatoGerador`, `valorServico`

> ⚠️ **Erro 400:** PIS/COFINS após 2027; ISS após 2033.

---

## 🟦 Grupo 4 — Pedágio

### 4.1 `POST /calculadora/pedagio`
> **operationId:** `calcularTributo` · **summary:** "Cálculo do tributo (Pedágio)"

**Descrição:** Calcula tributos para **operações de pedágio** (NFS-e Via — exploração de via). Considera múltiplos trechos (`trechos[]`), cada trecho com sua extensão, UF e município.

**Request:** [`PedagioInput`](02-schemas.md#pedagioinput)
**Response 200:** [`PedagioOutput`](02-schemas.md#pedagiooutput)

**Campos obrigatórios:** `dataHoraEmissao`, `codigoMunicipioOrigem`, `ufMunicipioOrigem`, `cst`, `cClassTrib`, `baseCalculo`, `trechos[]`

---

## 🟪 Grupo 5 — Dados Abertos (tabelas auxiliares)

> Todos os endpoints `GET` aceitam parâmetro `data` no formato **ISO 8601** (`yyyy-MM-dd`) — habilita consulta histórica.

### 5.1 `GET /calculadora/dados-abertos/versao`
> **operationId:** `consultarVersao`

Retorna a versão do app e do banco. **Use como health-check.**
Response: [`VersaoOutput`](02-schemas.md#versaooutput)

### 5.2 `GET /calculadora/dados-abertos/ufs`
> **operationId:** `consultarUfs`

Lista todas as 27 UFs (sigla, nome, código IBGE).
Response: [`UfDadosAbertosOutput[]`](02-schemas.md#ufdadosabertosoutput)

### 5.3 `GET /calculadora/dados-abertos/ufs/municipios?siglaUf={UF}`
> **operationId:** `consultarMunicipiosPorSiglaUf`

Lista os municípios de uma UF (código IBGE + nome).
Response: [`MunicipioDadosAbertosOutput[]`](02-schemas.md#municipiodadosabertosoutput)

### 5.4 `GET /calculadora/dados-abertos/situacoes-tributarias/cbs-ibs?data=YYYY-MM-DD`
> **operationId:** `consultarSituacoesTributariasCbsIbs`

Lista os **CST** vigentes na data informada para CBS/IBS.
Response: [`SituacaoTributariaDadosAbertosOutput[]`](02-schemas.md#situacaotributariadadosabertosoutput)

### 5.5 `GET /calculadora/dados-abertos/situacoes-tributarias/imposto-seletivo?data=YYYY-MM-DD`
> **operationId:** `consultarSituacoesTributariasImpostoSeletivo`

Lista os **CST** do Imposto Seletivo.

### 5.6 `GET /calculadora/dados-abertos/ncm?ncm={code}&data=YYYY-MM-DD`
> **operationId:** `consultarNcm`

Consulta um código **NCM** específico — retorna se é tributado pelo IS, alíquotas ad valorem/ad rem, capítulo/posição/subposição/item/subitem/unidade.
Response: [`NcmDadosAbertosOutput`](02-schemas.md#ncmdadosabertosoutput)

### 5.7 `GET /calculadora/dados-abertos/nbs?nbs={code}&data=YYYY-MM-DD`
> **operationId:** `consultarNbs`

Consulta um código **NBS** específico (Nomenclatura Brasileira de Serviços).
Response: [`NbsDadosAbertosOutput`](02-schemas.md#nbsdadosabertosoutput)

### 5.8 `GET /calculadora/dados-abertos/fundamentacoes-legais?data=YYYY-MM-DD`
> **operationId:** `consultarFundamentacoesLegais`

Retorna fundamentação legal vinculada às classificações tributárias (texto + texto curto + referência normativa).
Response: [`FundamentacaoClassificacaoDadosAbertosOutput[]`](02-schemas.md#fundamentacaoclassificacaodadosabertosoutput)

### 5.9 `GET /calculadora/dados-abertos/classificacoes-tributarias/cbs-ibs?data=YYYY-MM-DD`
> **operationId:** `consultarClassificacoesTributariasCbsIbs`

Lista **TODAS** as classificações tributárias (cClassTrib) vigentes para CBS/IBS na data.
Response: [`ClassificacaoTributariaDadosAbertosOutput[]`](02-schemas.md#classificacaotributariadadosabertosoutput)

### 5.10 `GET /calculadora/dados-abertos/classificacoes-tributarias/cbs-ibs/{cst}?data=YYYY-MM-DD`
> **operationId:** `listarPorCstCbsIbs`

Lista os **cClassTrib** vinculados a um CST específico.
Path: `cst` (string)

### 5.11 `GET /calculadora/dados-abertos/classificacoes-tributarias/cbs-ibs/{siglaDfe}/{cClassTrib}?data=YYYY-MM-DD`
> **operationId:** `consultarValidadeDfeClassificacaoTributaria`

Verifica se um cClassTrib é válido para um determinado tipo de DFe na data.
Path: `siglaDfe` (`NFe`, `NFCe`, `NFSe`, etc.), `cClassTrib` (string)
Response: [`ValidadeDfeClassificacaoTributariaDadosAbertosOutput`](02-schemas.md#validadedfeclassificacaotributariadadosabertosoutput)

> 💡 **Use case Tributiq:** Validar antecipadamente, na emissão, se o cClassTrib escolhido pelo usuário é válido para o tipo de nota — evita rejeição na SEFAZ.

### 5.12 `GET /calculadora/dados-abertos/classificacoes-tributarias/imposto-seletivo?data=YYYY-MM-DD`
> **operationId:** `consultarClassificacoesTributariasImpostoSeletivo`

Lista todos os cClassTrib do Imposto Seletivo.

### 5.13 `GET /calculadora/dados-abertos/classificacoes-tributarias/imposto-seletivo/{cst}?data=YYYY-MM-DD`
> **operationId:** `listarPorCstImpostoSeletivo`

Lista cClassTrib do IS por CST.

### 5.14 `GET /calculadora/dados-abertos/classificacoes-tributarias/{idSituacaoTributaria}?data=YYYY-MM-DD`
> ⚠️ **DEPRECATED**

Endpoint legado — usar 5.10 ou 5.13.

### 5.15 `GET /calculadora/dados-abertos/aliquota-uniao?data=YYYY-MM-DD`
> **operationId:** `consultarAliquotaUniao`

Retorna a **alíquota da União (CBS)** vigente na data.
Response: [`AliquotaDadosAbertosOutput`](02-schemas.md#aliquotadadosabertosoutput) → `{aliquotaReferencia, aliquotaPropria, formaAplicacao}`

### 5.16 `GET /calculadora/dados-abertos/aliquota-uf?codigoUf={int}&data=YYYY-MM-DD`
> **operationId:** `consultarAliquotaUf`

Retorna a **alíquota de IBS da UF**.

### 5.17 `GET /calculadora/dados-abertos/aliquota-municipio?codigoMunicipio={int}&data=YYYY-MM-DD`
> **operationId:** `consultarAliquotaMunicipio`

Retorna a **alíquota de IBS Municipal** (código IBGE de 7 dígitos, ex: `4314902`=Porto Alegre).

---

## 🛡️ Tratamento de Erros — `ProblemDetail` (RFC 7807)

Todos os erros retornam `application/problem+json`:

```json
{
  "type": "about:blank",
  "title": "Bad Request",
  "status": 400,
  "detail": "Campo 'pis' incompatível com anoFatoGerador=2028 (PIS extinto a partir de 2027)",
  "instance": "/servico/calcular-tributos-consumo/api/calculadora/base-calculo/cbs-ibs-mercadorias",
  "properties": { "field": "pis", "year": 2028 }
}
```

**Mapeamento sugerido para Tributiq (Python):**

```python
class CalculadoraError(Exception):
    def __init__(self, problem: dict):
        self.type = problem.get("type")
        self.title = problem.get("title")
        self.status = problem.get("status")
        self.detail = problem.get("detail")
        self.instance = problem.get("instance")
        self.properties = problem.get("properties", {})
        super().__init__(f"[{self.status}] {self.title}: {self.detail}")
```

---

## 📊 Matriz de Decisão — Qual endpoint usar?

| Cenário | Endpoint |
|---|---|
| Calcular tributos completos de uma venda mercantil (NF-e) | `POST /calculadora/regime-geral` |
| Calcular tributos de prestação de serviço (NFS-e) | `POST /calculadora/regime-geral` (item com `nbs`) |
| Apenas saber a BC do CIBS (sem cálculo do imposto) | `POST /calculadora/base-calculo/cbs-ibs-mercadorias` |
| Calcular IS isolado (ex: cigarro/bebida) | `POST /calculadora/base-calculo/is-mercadorias` |
| Cálculo específico de NFS-e com deduções de imóvel/saúde | `POST /calculadora/nfse/base-calculo` |
| Concessionária de pedágio | `POST /calculadora/pedagio` |
| Validar XML antes de transmitir à SEFAZ | `POST /calculadora/xml/validate` |
| Gerar XML a partir do ROC calculado | `POST /calculadora/xml/generate` |
| Carregar tabelas para cache local | `GET /calculadora/dados-abertos/*` |
| Health check / monitoring | `GET /calculadora/dados-abertos/versao` |
