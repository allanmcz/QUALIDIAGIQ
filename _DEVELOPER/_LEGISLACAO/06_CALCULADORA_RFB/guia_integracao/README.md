# Documentação da Calculadora de Tributos sobre Consumo

## Bem-vindo à pasta CALCULADORA_MANUS

Esta pasta contém a documentação completa e estruturada da **Calculadora de Tributos sobre Consumo (Beta)** do Portal Nacional de Tributação de Bens e Serviços.

### Arquivos Disponíveis

#### 1. **swagger_api_calculadora.md**
Documentação técnica completa da API OpenAPI (v0, OAS 3.1) que alimenta a Calculadora.

**Conteúdo:**
*   Visão geral da API
*   Servidor base e endpoints disponíveis
*   Organização por categorias de serviço:
    *   Base de Cálculo (VERSÃO BETA)
    *   Calculadora (VERSÃO BETA)
    *   NFS-e (VERSÃO BETA)
    *   Dados Abertos (VERSÃO BETA)
    *   Pedágio (VERSÃO BETA)
*   Descrição de todos os modelos de dados (schemas)

**Quando usar:**
*   Para entender a estrutura técnica da API
*   Para consultar endpoints disponíveis
*   Para integração programática com a calculadora
*   Para referência de modelos de dados

---

#### 2. **guia_integracao_calculadora.md**
Guia prático completo para integração de sistemas ERP com a Calculadora.

**Conteúdo:**
*   Objetivo e estrutura de pastas
*   Fluxo completo de integração em 4 passos
*   Scripts Python prontos para uso:
    *   Passo 1: Cálculo de tributos (regime-geral)
    *   Passo 2: Geração de XML
    *   Passo 3: Validação de XML
    *   Passo 4: Injeção de RTC em documento fiscal
*   Exemplos de entrada e saída
*   Instruções de execução (manual e automatizada)
*   Guia de adaptação para seu ERP
*   Tratamento de erros com retry
*   Endpoints da API utilizados

**Quando usar:**
*   Para implementar integração com ERP
*   Para entender o fluxo de processamento
*   Para adaptar scripts para seu sistema
*   Para referência de exemplos de código

---

### Estrutura de Uso

#### Para Consultores Tributários
1.  Comece pelo **swagger_api_calculadora.md** para entender a estrutura técnica
2.  Use o **guia_integracao_calculadora.md** para compreender o fluxo operacional
3.  Consulte os endpoints para validar requisitos de integração

#### Para Desenvolvedores
1.  Revise o **guia_integracao_calculadora.md** para entender o fluxo completo
2.  Copie os scripts Python como base para sua implementação
3.  Consulte o **swagger_api_calculadora.md** para detalhes técnicos da API
4.  Adapte os scripts conforme necessário para seu ERP

#### Para Gestores de Projeto
1.  Leia o **guia_integracao_calculadora.md** para entender as fases de integração
2.  Use os 4 passos como base para planejamento de projeto
3.  Consulte "Próximos Passos" para definir cronograma

---

### Informações Técnicas

**Versão da Documentação:** Baseada em dados de 26/04/2026

**API Base:** `https://consumo.tributos.gov.br:57374/servico/calcular-tributos-consumo/api`

**Linguagem dos Scripts:** Python 3.7+

**Dependências Principais:** `requests`, `json`, `xml.etree.ElementTree`

---

### Fluxo de Integração em 4 Passos

```
┌─────────────────────────────────────────────────────────────────┐
│ Passo 1: Calcular Tributos (regime-geral.py)                   │
│ Entrada: JSON com dados da operação                            │
│ Saída: JSON com CBS, IBS e IS calculados                       │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ Passo 2: Gerar XML (gerar-xml.py)                              │
│ Entrada: JSON com resultado do cálculo                         │
│ Saída: XML com grupos de tributação (IS, IBSCBS, etc)         │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ Passo 3: Validar XML (validar-grupo-xml.py)                    │
│ Entrada: XML gerado                                            │
│ Saída: Resultado da validação (sucesso ou erros)              │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ Passo 4: Injetar XML (injetar-xml.py)                          │
│ Entrada: XML RTC + NFe sem RTC                                 │
│ Saída: NFe completa com grupos de tributação                   │
└─────────────────────────────────────────────────────────────────┘
```

---

### Endpoints Principais

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/calculadora/regime-geral` | POST | Cálculo de tributos (CBS, IBS, IS) |
| `/calculadora/xml/generate` | POST | Geração de XML com grupos RTC |
| `/calculadora/xml/validate` | POST | Validação de XML gerado |
| `/calculadora/nfse/base-calculo` | POST | Base de cálculo para NFS-e |
| `/calculadora/dados-abertos/versao` | GET | Versão do aplicativo |
| `/calculadora/dados-abertos/ncm` | GET | Nomenclatura Comum do Mercosul |
| `/calculadora/dados-abertos/nbs` | GET | Nomenclatura Brasileira de Serviços |

---

### Próximos Passos Recomendados

1.  **Testar os scripts** com dados de exemplo
2.  **Adaptar para seu ERP** conforme estrutura de dados
3.  **Integrar no fluxo** de emissão de documentos fiscais
4.  **Validar em homologação** antes de produção
5.  **Implementar em produção** com monitoramento

---

### Suporte e Referências

*   **Portal Oficial:** [Consumo Tributos](https://consumo.tributos.gov.br)
*   **Documentação API:** [Swagger UI](https://consumo.tributos.gov.br/servico/calcular-tributos-consumo/api/swagger-ui/index.html)
*   **Guia de Integração:** [Guia Prático](https://consumo.tributos.gov.br/servico/calcular-tributos-consumo/calculadora/documentacao/guia-integracao)

---

**Última atualização:** 26 de abril de 2026
