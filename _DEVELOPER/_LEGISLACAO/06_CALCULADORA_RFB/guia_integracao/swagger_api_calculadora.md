# Documentação da API - Calculadora de Tributos sobre Consumo (Beta)

**Fonte:** [Swagger UI - Consumo Tributos](https://consumo.tributos.gov.br/servico/calcular-tributos-consumo/api/swagger-ui/index.html)

## Visão Geral
Esta é a documentação OpenAPI (v0, OAS 3.1) para o serviço de cálculo de tributos sobre consumo, disponibilizada pelo Portal Nacional de Tributação de Bens e Serviços.

**Servidor Base:** `https://consumo.tributos.gov.br:57374/servico/calcular-tributos-consumo/api`

---

## Endpoints Disponíveis

### 1. Base de Cálculo - VERSÃO BETA
Serviço para Base de Cálculo.

*   **POST** `/calculadora/base-calculo/is-mercadorias`
    *   **Descrição:** Cálculo para Imposto Seletivo.
*   **POST** `/calculadora/base-calculo/cbs-ibs-mercadorias`
    *   **Descrição:** Cálculo para CIBS.

### 2. Calculadora - VERSÃO BETA
Calculadora de Tributos.

*   **GET** `/calculadora/xml/validate`
    *   **Descrição:** Consulta tipos de DFe para validação.
*   **GET** `/calculadora/xml/generate`
    *   **Descrição:** Consulta tipos de DFe para geração.
*   **POST** `/calculadora/xml/validate`
    *   **Descrição:** Validação de XML.
*   **POST** `/calculadora/xml/generate`
    *   **Descrição:** Geração de XML.
*   **POST** `/calculadora/regime-geral`
    *   **Descrição:** Cálculo do tributo (Regime Geral).

### 3. NFS-e - VERSÃO BETA
Serviço para cálculo de Base de Cálculo de NFS-e.

*   **POST** `/calculadora/nfse/base-calculo`
    *   **Descrição:** Base de Cálculo NFS-e.

### 4. Dados Abertos - VERSÃO BETA
Consultas para os Dados Abertos.

*   **GET** `/calculadora/dados-abertos/versao`
    *   **Descrição:** Versão do Aplicativo e do Banco de Dados.
*   **GET** `/calculadora/dados-abertos/ufs`
    *   **Descrição:** Consulta de Unidade Federativa.
*   **GET** `/calculadora/dados-abertos/ufs/municipios`
    *   **Descrição:** Consulta de Município.
*   **GET** `/calculadora/dados-abertos/situacoes-tributarias/imposto-seletivo`
    *   **Descrição:** Situação Tributária (CST) para Imposto Seletivo.
*   **GET** `/calculadora/dados-abertos/situacoes-tributarias/cbs-ibs`
    *   **Descrição:** Situação Tributária (CST) para CBS/IBS.
*   **GET** `/calculadora/dados-abertos/ncm`
    *   **Descrição:** Nomenclatura Comum do Mercosul (NCM).
*   **GET** `/calculadora/dados-abertos/nbs`
    *   **Descrição:** Nomenclatura Brasileira de Serviços (NBS).
*   **GET** `/calculadora/dados-abertos/fundamentacoes-legais`
    *   **Descrição:** Fundamentação Legal.
*   **GET** `/calculadora/dados-abertos/classificacoes-tributarias/{idSituacaoTributaria}`
    *   **Descrição:** Classificação Tributária (cClassTrib) - *DEPRECATED*.
*   **GET** `/calculadora/dados-abertos/classificacoes-tributarias/imposto-seletivo`
    *   **Descrição:** Classificação Tributária (cClassTrib) para Imposto Seletivo.
*   **GET** `/calculadora/dados-abertos/classificacoes-tributarias/imposto-seletivo/{cst}`
    *   **Descrição:** Classificações Tributárias por CST - Imposto Seletivo.
*   **GET** `/calculadora/dados-abertos/classificacoes-tributarias/cbs-ibs`
    *   **Descrição:** Classificação Tributária (cClassTrib) para CBS/IBS.
*   **GET** `/calculadora/dados-abertos/classificacoes-tributarias/cbs-ibs/{siglaDfe}/{cClassTrib}`
    *   **Descrição:** Classificação Tributária CBS/IBS por DFe e cClassTrib.
*   **GET** `/calculadora/dados-abertos/classificacoes-tributarias/cbs-ibs/{cst}`
    *   **Descrição:** Classificações Tributárias por CST - CBS/IBS.
*   **GET** `/calculadora/dados-abertos/aliquota-uniao`
    *   **Descrição:** Alíquota Padrão ou de Referência.
*   **GET** `/calculadora/dados-abertos/aliquota-uf`
    *   **Descrição:** Alíquota Padrão ou de Referência para IBS Estadual.
*   **GET** `/calculadora/dados-abertos/aliquota-municipio`
    *   **Descrição:** Alíquota Padrão ou de Referência para IBS Municipal.

### 5. Pedágio - VERSÃO BETA
IVA - Calculadora de Tributos para o Pedágio.

*   **POST** `/calculadora/pedagio`
    *   **Descrição:** Cálculo do tributo para pedágio.

---

## Schemas (Modelos de Dados)
A API utiliza os seguintes modelos de dados principais para requisições e respostas:

*   `ProblemDetail`
*   `AjusteCompetenciaDomain`
*   `CBSDomain`
*   `CBSTotalDomain`
*   `CreditoPresumidoIBSZFMDomain`
*   `CreditoPresumidoOperacaoDomain`
*   `DevolucaoTributosDomain`
*   `DiferimentoDomain`
*   `EstornoCreditoDomain`
*   `GrupoIBSCBSDomain`
*   `IBSCBSCreditoPresumidoDomain`
*   `IBSCBSDomain`
*   `IBSCBSTotalDomain`
*   `IBSMunDomain`
*   `IBSMunTotalDomain`
*   `IBSTotalDomain`
*   `IBSUFDomain`
*   `IBSUFTotalDomain`
*   `ImpostoSeletivoDomain`
*   `ImpostoSeletivoTotalDomain`
*   `MonofasiaDiferimentoDomain`
*   `MonofasiaDomain`
*   `MonofasiaPadraoDomain`
*   `MonofasiaRetencaoDomain`
*   `MonofasiaRetidoAnteriormenteDomain`
*   `MonofasiaTotalDomain`
*   `ObjetoDomain`
*   `ROCDomain`
*   `ReducaoAliquotaDomain`
*   `TransferenciaCreditoDomain`
*   `TributacaoCompraGovernamentalDomain`
*   `TributacaoRegularDomain`
*   `TributosDomain`
*   `TributosTotaisDomain`
*   `ValoresTotaisDomain`
*   `ImpostoSeletivoInput`
*   `ItemOperacaoInput`
*   `OperacaoInput`
*   `TributacaoRegularInput`
*   `PedagioInput`
*   `TrechoPedagioInput`
*   `PedagioOutput`
*   `TotalPedagioOutput`
*   `TrechoPedagioOutput`
*   `TributoPedagioOutput`
*   `TributoTotalPedagioOutput`
*   `NfseBaseCalculoInput`
*   `NfseBaseCalculoOutput`
*   `BaseCalculoISMercadoriasInput`
*   `BaseCalculoISMercadoriasModel`
*   `BaseCalculoCibsInput`
*   `TipoDocumentoDTO`
*   `VersaoOutput`
*   `UfDadosAbertosOutput`
*   `MunicipioDadosAbertosOutput`
*   `SituacaoTributariaDadosAbertosOutput`
*   `NcmDadosAbertosOutput`
*   `NbsDadosAbertosOutput`
*   `FundamentacaoClassificacaoDadosAbertosOutput`
*   `ClassificacaoTributariaDadosAbertosOutput`
*   `TipoDfeClassificacaoDadosAbertosOutput`
*   `ValidadeDfeClassificacaoTributariaDadosAbertosOutput`
*   `AliquotaDadosAbertosOutput`
