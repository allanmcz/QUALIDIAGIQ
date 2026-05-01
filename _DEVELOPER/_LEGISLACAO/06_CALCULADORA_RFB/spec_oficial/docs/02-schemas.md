# 02 — Catálogo de Schemas (DTOs)

> **Total:** 63 schemas · **OpenAPI 3.1.0** · Origem: `raw/openapi.json`

Os schemas estão agrupados por **família funcional** para facilitar a navegação. Para a definição RAW completa, consulte `raw/openapi.json` no nó `components.schemas`.

---

## 📥 Inputs (Entrada)

### `OperacaoInput`
Objeto raiz do `POST /calculadora/regime-geral`.

| Campo | Tipo | Obrigatório | Descrição | Exemplo |
|---|---|---|---|---|
| `id` | string | ✅ | Identificador do ROC (UUID/hash) | `6194602ea71cbf9431c236de4409d920` |
| `versao` | string | ✅ | Versão do schema do ROC | `0.0.1` |
| `municipio` | int64 | ✅ | Código IBGE do município | `4314902` |
| `itens[]` | `ItemOperacaoInput[]` | ✅ | Itens da operação | — |
| `dhFatoGerador` | datetime ISO | — | Data/hora do fato gerador (UTC ou com offset) | `2026-01-01T09:50:05-03:00` |
| `dataHoraEmissao` | datetime ISO | — | ⚠️ **Será removido** — usar `dhFatoGerador` | — |
| `uf` | string(2) | — | Sigla da UF | `RS` |

### `ItemOperacaoInput`
Item individual dentro de uma operação.

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `numero` | int32 | ✅ | Número sequencial do item |
| `cst` | string(3) | ✅ | Código de Situação Tributária |
| `cClassTrib` | string(6) | ✅ | Código de Classificação Tributária |
| `ncm` | string | — | Código NCM (mercadorias) |
| `nbs` | string | — | Código NBS (serviços) |
| `baseCalculo` | number | — | Base de cálculo |
| `quantidade` | number | — | Quantidade |
| `unidade` | string | — | Unidade de medida (ex: `LT`, `KG`) |
| `impostoSeletivo` | `ImpostoSeletivoInput` | — | Bloco IS (se aplicável) |
| `tributacaoRegular` | `TributacaoRegularInput` | — | Bloco de tributação regular |

### `TributacaoRegularInput`
| Campo | Tipo | Obrigatório |
|---|---|---|
| `cst` | string(3) | ✅ |
| `cClassTrib` | string(6) | ✅ |

### `ImpostoSeletivoInput`
| Campo | Tipo | Obrigatório |
|---|---|---|
| `cst` | string(3) | ✅ |
| `cClassTrib` | string(6) | ✅ |
| `baseCalculo` | number | ✅ |
| `impostoInformado` | number | ✅ |
| `quantidade` | number | — |
| `unidade` | string | — |

### `BaseCalculoCibsInput`
Entrada do `POST /base-calculo/cbs-ibs-mercadorias`. Modela a fórmula da BC do CIBS conforme arts. 12 e 13 da LC 214/2025.

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `anoFatoGerador` | int32 | ✅ | Ano (2026, 2027, ...) |
| `valorBem` | number | — | Valor do bem antes de ajustes |
| `ajusteAcrescimos` | number | — | Acréscimos |
| `juros` | number | — | Juros |
| `multas` | number | — | Multas |
| `encargos` | number | — | Encargos |
| `frete` | number | — | Frete cobrado como parte do valor |
| `impostoSeletivo` | number | — | IS (compõe a BC do CIBS) |
| `outrosTributos` | number | — | Tributos exceto CBS/IBS |
| `demaisImportancias` | number | — | Demais importâncias (seguros, taxas) |
| `icms` | number | — | ICMS (até 2032) |
| `iss` | number | — | ISS (até 2032) |
| `pis` | number | — | PIS (até 2026) |
| `pisImportacao` | number | — | PIS Importação |
| `cofins` | number | — | COFINS (até 2026) |
| `cofinsImportacao` | number | — | COFINS Importação |
| `cosip` | number | — | COSIP |
| `ipi` | number | — | IPI |
| `descontoIncondicional` | number | — | Desconto incondicional |

### `BaseCalculoISMercadoriasInput`
Igual ao `BaseCalculoCibsInput`, **exceto:**
- ❌ Não aceita: `pis`, `pisImportacao`, `cofins`, `cofinsImportacao` (CBS/IBS já não compõem a BC do IS)
- ✅ Aceita adicionalmente: `bonificacao` e `devolucaoVendas` (art. 417 §2º e art. 418)
- O campo `frete` aqui se chama `freteCobrado`

### `NfseBaseCalculoInput`
| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `anoFatoGerador` | int32 | ✅ | |
| `valorServico` | number | ✅ | Valor do serviço prestado |
| `descontoIncondicional` | number | — | |
| `vCalcReeRepRes` | number | — | Reembolso/repasse/ressarcimento (não integra BC) |
| `vCalcDedRedIBSCBS` | number | — | Deduções/reduções (locação, cessão, arrendamento de imóveis, serviços médicos) |
| `iss`, `pis`, `cofins` | number | — | Tributos a serem excluídos da BC |

### `PedagioInput`
| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `dataHoraEmissao` | datetime | ✅ | |
| `codigoMunicipioOrigem` | int64 | ✅ | IBGE |
| `ufMunicipioOrigem` | string(2) | ✅ | |
| `cst` | string(3) | ✅ | |
| `cClassTrib` | string(6) | ✅ | |
| `baseCalculo` | number | ✅ | |
| `trechos[]` | `TrechoPedagioInput[]` | ✅ | Lista de trechos percorridos |

### `TrechoPedagioInput`
| Campo | Tipo | Obrigatório |
|---|---|---|
| `numero` | int32 | ✅ |
| `municipio` | int64 (IBGE) | ✅ |
| `uf` | string(2) | ✅ |
| `extensao` | number (km) | ✅ |

---

## 📤 Outputs Principais

### `ROCDomain` — Recibo da Operação de Consumo
**Objeto-chave da API**. Saída do `/regime-geral` e entrada do `/xml/generate`.

| Campo | Tipo | Descrição |
|---|---|---|
| `objetos[]` | `ObjetoDomain[]` | Itens calculados |
| `total` | `ValoresTotaisDomain` | Totalizadores |

### `ObjetoDomain`
Item individual calculado, contendo:
- `tributos: TributosDomain` → bloco com `IBSCBSDomain` + `ImpostoSeletivoDomain`

### `IBSCBSDomain`
Bloco de **CBS + IBS** por item, conforme NT 2025.002 do Portal NF-e.

| Campo | Tipo | Descrição |
|---|---|---|
| `CST` | string | Código situação tributária |
| `cClassTrib` | string | Código de classificação tributária |
| `indDoacao` | int | Indica natureza de doação |
| `gIBSCBS` | `GrupoIBSCBSDomain` | Grupo principal |
| `gIBSCBSMono` | `MonofasiaDomain` | Monofasia |
| `gTransfCred` | `TransferenciaCreditoDomain` | Transferência de crédito |
| `gAjusteCompet` | `AjusteCompetenciaDomain` | Ajuste de competência |
| `gEstornoCred` | `EstornoCreditoDomain` | Estorno de crédito |
| `gCredPresOper` | `CreditoPresumidoOperacaoDomain` | Crédito presumido da operação |
| `gCredPresIBSZFM` | `CreditoPresumidoIBSZFMDomain` | Crédito presumido ZFM |

### `GrupoIBSCBSDomain`
| Campo | Tipo | Descrição |
|---|---|---|
| `vBC` | number | Base de cálculo do IBS+CBS |
| `gIBSUF` | `IBSUFDomain` | Detalhamento IBS Estadual |
| `gIBSMun` | `IBSMunDomain` | Detalhamento IBS Municipal |
| `vIBS` | number | Valor total do IBS |
| `gCBS` | `CBSDomain` | Detalhamento CBS |
| `gTribRegular` | `TributacaoRegularDomain` | Tributação regular |
| `gTribCompraGov` | `TributacaoCompraGovernamentalDomain` | Compra governamental |

### `ImpostoSeletivoDomain`
| Campo | Tipo | Descrição |
|---|---|---|
| `CSTIS` | string | CST do IS |
| `cClassTribIS` | string | cClassTrib do IS |
| `vBCIS` | number | BC do IS |
| `pIS` | number | Alíquota ad valorem |
| `pISEspec` | number | Alíquota específica (ad rem) |
| `uTrib` | string | Unidade tributável |
| `qTrib` | number | Quantidade tributável |
| `vIS` | number | Valor do IS calculado |
| `memoriaCalculo` | string | Memória de cálculo |

### `PedagioOutput`
Saída do cálculo de pedágio:
- `dataHoraEmissao`, `municipioOrigem`, `ufMunicipioOrigem`, `cst`, `cClassTrib`, `baseCalculo`, `extensaoTotal`
- `trechos[]: TrechoPedagioOutput[]` — cada trecho com seus tributos
- `total: TotalPedagioOutput` — totais consolidados

### `NfseBaseCalculoOutput`
```json
{ "baseCalculo": 100.55 }
```

### `BaseCalculoISMercadoriasModel`
```json
{ "baseCalculo": 100.55 }
```

---

## 📋 Outputs de Dados Abertos

### `VersaoOutput`
| Campo | Tipo | Exemplo |
|---|---|---|
| `versaoApp` | string | `0.0.0-SNAPSHOT` |
| `versaoDb` | string | `1.0.0` |
| `descricaoVersaoDb` | string | `Versão de homologação` |
| `dataVersaoDb` | string | `2026-01-01` |
| `ambiente` | string | `Online` |

### `UfDadosAbertosOutput`
| Campo | Tipo | Exemplo |
|---|---|---|
| `sigla` | string | `RS` |
| `nome` | string | `Rio Grande do Sul` |
| `codigo` | int64 | `43` |

### `MunicipioDadosAbertosOutput`
| Campo | Tipo | Exemplo |
|---|---|---|
| `codigo` | int64 (IBGE 7 dígitos) | `4314902` |
| `nome` | string | `Porto Alegre` |

### `SituacaoTributariaDadosAbertosOutput`
| Campo | Tipo | Exemplo |
|---|---|---|
| `id` | int64 | `0` |
| `codigo` | string | `000` |
| `descricao` | string | `Tributação Integral` |

### `ClassificacaoTributariaDadosAbertosOutput`
**18 campos** — schema mais rico de Dados Abertos. Principais:

| Campo | Tipo | Descrição |
|---|---|---|
| `codigo` | string | cClassTrib |
| `descricao` | string | |
| `tipoAliquota` | string | |
| `nomenclatura` | string | |
| `descricaoTratamentoTributario` | string | |
| `incompativelComSuspensao` | bool | |
| `exigeGrupoDesoneracao` | bool | |
| `possuiPercentualReducao` | bool | |
| `indicaApropriacaoCreditoAdquirenteCbs` | bool | |
| `indicaApropriacaoCreditoAdquirenteIbs` | bool | |
| `indicaCreditoPresumidoFornecedor` | bool | |
| `indicaCreditoPresumidoAdquirente` | bool | |
| `creditoOperacaoAntecedente` | string | |
| `percentualReducaoCbs` | number | |
| `percentualReducaoIbsUf` | number | |
| `percentualReducaoIbsMun` | number | |
| `tiposDfeClassificacao[]` | array | DFes válidos |
| `dataAtualizacao` | date | YYYY-MM-DD |

### `NcmDadosAbertosOutput`
| Campo | Tipo |
|---|---|
| `tributadoPeloImpostoSeletivo` | bool |
| `aliquotaAdValorem` | number |
| `aliquotaAdRem` | number |
| `capitulo`, `posicao`, `subposicao`, `item`, `subitem`, `unidade` | string |

### `NbsDadosAbertosOutput`
| Campo | Tipo |
|---|---|
| `tributadoPeloImpostoSeletivo` | bool |
| `aliquotaAdValorem` | number |
| `capitulo`, `posicao`, `subposicao1`, `subposicao2`, `item` | string |

### `AliquotaDadosAbertosOutput`
| Campo | Tipo | Descrição |
|---|---|---|
| `aliquotaReferencia` | number | Alíquota de referência |
| `aliquotaPropria` | number | Alíquota própria do ente |
| `formaAplicacao` | enum | `SUBSTITUICAO` \| `ACRESCIMO` \| `DECRESCIMO` |

### `FundamentacaoClassificacaoDadosAbertosOutput`
Vincula cClassTrib e CST à fundamentação legal (LC 214, NT etc.):
- `codigoClassificacaoTributaria`, `descricaoClassificacaoTributaria`
- `codigoSituacaoTributaria`, `descricaoSituacaoTributaria`
- `conjuntoTributo` (ex: `"CBS e IBS"`)
- `texto`, `textoCurto`, `referenciaNormativa`

### `ValidadeDfeClassificacaoTributariaDadosAbertosOutput`
| Campo | Tipo | Exemplo |
|---|---|---|
| `siglaDfeInformado` | string | `NFSe` |
| `validoParaSiglaDfeInformado` | bool | `true` |
| `nomenclatura` | string | `NBS ou NCM` |
| `exigeGrupoTributacaoRegular` | bool | `false` |
| `permiteDiferimento` | bool | `false` |

### `TipoDocumentoDTO`
Resposta do `GET /xml/validate` e `GET /xml/generate`:
- `sigla`, `descricao`, `subtipos[]`

---

## ⚠️ Erro Padrão — `ProblemDetail` (RFC 7807)

Conforme RFC 7807 (Problem Details for HTTP APIs):

| Campo | Tipo | Descrição |
|---|---|---|
| `type` | URI | Identificador do tipo de erro |
| `title` | string | Resumo curto |
| `status` | int32 | HTTP status code |
| `detail` | string | Descrição detalhada |
| `instance` | URI | URI da instância que produziu o erro |
| `properties` | object | Campos extras (extensíveis) |

---

## 📚 Schemas Auxiliares Adicionais

> Estes schemas detalham componentes internos do `IBSCBSDomain` e `ROCDomain`. Consulte `raw/openapi.json` para a definição completa de cada um.

- `CBSDomain` — bloco CBS por item (alíquota, BC, valor, créditos)
- `CBSTotalDomain` — totais CBS
- `IBSUFDomain`, `IBSUFTotalDomain` — IBS estadual
- `IBSMunDomain`, `IBSMunTotalDomain` — IBS municipal
- `IBSTotalDomain`, `IBSCBSTotalDomain` — totalizadores combinados
- `MonofasiaDomain` (e variantes: `MonofasiaPadraoDomain`, `MonofasiaRetencaoDomain`, `MonofasiaRetidoAnteriormenteDomain`, `MonofasiaDiferimentoDomain`, `MonofasiaTotalDomain`)
- `TransferenciaCreditoDomain`, `EstornoCreditoDomain`, `AjusteCompetenciaDomain`
- `CreditoPresumidoOperacaoDomain`, `CreditoPresumidoIBSZFMDomain`, `IBSCBSCreditoPresumidoDomain`
- `TributacaoRegularDomain`, `TributacaoCompraGovernamentalDomain`
- `DiferimentoDomain`, `ReducaoAliquotaDomain`, `DevolucaoTributosDomain`
- `TributosDomain`, `TributosTotaisDomain`, `ValoresTotaisDomain`
- `ImpostoSeletivoTotalDomain`
- `TipoDfeClassificacaoDadosAbertosOutput` — DFes válidos por classificação
- `TrechoPedagioOutput`, `TotalPedagioOutput`, `TributoPedagioOutput`, `TributoTotalPedagioOutput`

> 💡 **Dica de mapeamento Tributiq:** Em Python, gere os Pydantic models a partir do `openapi.json` usando `datamodel-code-generator`:
> ```bash
> datamodel-codegen --input raw/openapi.json --input-file-type openapi \
>   --output src/infrastructure/calculadora_rfb/dto.py --output-model-type pydantic_v2.BaseModel
> ```
