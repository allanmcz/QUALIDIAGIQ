# Acoes por Segmento

## Visao geral do questionario adaptativo

O catalogo possui 37 perguntas, mas a exibicao muda por setor, porte e regime. O segmento ainda influencia mais o **questionario** do que o **plano final**; a recomendacao e levar essa mesma segmentacao para o motor de acoes.

## Comercio / Varejo / Atacado

| Eixo | Acoes prioritarias |
|---|---|
| Fiscal | Simular margem por categoria; mapear ICMS-ST; classificar cesta basica, produtos com reducao e produtos com possivel Imposto Seletivo. |
| Tecnologia | Validar cClassTrib, cCredPres, XML de NF-e/NFC-e e integracoes de PDV/retaguarda. |
| Financeiro | Avaliar giro de estoque e capital de giro em funcao da mudanca de creditos. |
| Operacional | Revisar processo pedido-faturamento-devolucao e dono do cadastro de itens. |
| Evidencias | Curva ABC por SKU, lista NCM/CST/cClassTrib, simulacao de margem e plano de homologacao. |

**Melhoria recomendada:** criar frente especifica "Varejo e ICMS-ST", porque hoje ela aparece apenas como pergunta fiscal e nao como bloco proprio no checklist.

## Industria

| Eixo | Acoes prioritarias |
|---|---|
| Fiscal | Mapear cadeia de insumos, energia, industrializacao, CD, filiais e destino. |
| Contabil | Avaliar plano de contas auxiliar para CBS/IBS e conciliacao SPED x razao. |
| Tecnologia | Homologar ERP/MRP/faturamento para classificacao fiscal e cenarios por UF. |
| Financeiro | Simular custo industrial e margem por familia de produto. |
| Evidencias | BOM/ficha tecnica, NCM por familia, memoria de calculo de creditos e simulacao por centro de custo. |

**Melhoria recomendada:** criar plano por cadeia industrial, separando compra de insumos, producao, expedicao e devolucao.

## Servicos

| Eixo | Acoes prioritarias |
|---|---|
| Fiscal | Homologar NFS-e no layout RTC e avaliar aliquota IBS+CBS sobre servicos. |
| Contratos | Revisar repasse tributario, reajuste, gross-up e retencoes. |
| Tecnologia | Validar integracao com emissor municipal/nacional e eventos CGNFS-e. |
| Financeiro | Simular margem por tipo de servico, contrato e local de prestacao. |
| Evidencias | XML/JSON NFS-e de teste, matriz de contratos, parecer de enquadramento em aliquota diferenciada. |

**Melhoria recomendada:** criar frente "NFS-e e contratos de servico", porque a natureza do risco e diferente da NF-e de mercadorias.

## Agro

| Eixo | Acoes prioritarias |
|---|---|
| Fiscal | Mapear reducao de aliquota agro, credito presumido produtor rural PF e apropriacao pela agroindustria. |
| Operacional | Controlar origem de produtos, produtor, cooperativa e documentos de aquisicao. |
| Financeiro | Projetar impacto em preco pago ao produtor, margem e repasse. |
| Compliance | Documentar controles de elegibilidade e rastreabilidade. |
| Evidencias | Cadastro produtor/produto, memoria de credito presumido, tabela produto x tratamento tributario. |

**Melhoria recomendada:** criar frente "Agro e credito presumido", com controles especificos por origem do produtor.

## Lucro Real medio/grande

| Eixo | Acoes prioritarias |
|---|---|
| Contabil | Avaliar reestruturacoes societarias, substituicao tributaria futura, IRPJ/CSLL e contratos longos. |
| Financeiro | Criar fluxo de caixa 2026-2033 com cenarios de aliquota. |
| Governanca | Elevar plano para comite executivo com auditoria, juridico e controladoria. |
| Tecnologia | Reforcar homologacao, trilhas de auditoria e integracoes entre ERP, fiscal e BI. |
| Evidencias | Ata de comite, modelo financeiro, parecer contabil, matriz de contratos e reconciliacao SPED. |

**Melhoria recomendada:** usar regime e porte para ajustar criticidade: lucro real medio/grande deveria receber criticidade minima alta em financeiro, contabil e governanca.

## Pequenas empresas / PME sem estrutura formal

| Eixo | Acoes prioritarias |
|---|---|
| Governanca | Nomear responsavel interno e contador externo como dupla minima de implantacao. |
| Fiscal | Priorizar cadastro fiscal, contratos e entendimento de impactos basicos. |
| Tecnologia | Confirmar com fornecedor do sistema fiscal/ERP quais atualizacoes serao entregues. |
| Treinamento | Trilha curta para dono, contador e operador fiscal. |
| Evidencias | Checklist simplificado, ata curta de decisao e calendario de revisao mensal. |

**Melhoria recomendada:** gerar plano em linguagem mais simples para dono de PME, sem perder base legal.

