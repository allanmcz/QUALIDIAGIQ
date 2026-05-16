# Acoes por Dimensao e Pergunta

## Como usar esta matriz

Cada linha abaixo traduz uma resposta fraca em uma acao de implantacao. No motor atual, essas acoes ainda nao sao materializadas pergunta a pergunta; elas servem como especificacao para evoluir o `ConsultoriaService` e o plano materializado.

Regra sugerida:

| Resposta | Tratamento |
|---|---|
| `nao` ou escala 1-2 | Criar acao obrigatoria com criticidade critica/alta. |
| `parcialmente` ou escala 3 | Criar acao de consolidacao com criticidade alta/media. |
| `sim` ou escala 4-5 | Nao criar acao corretiva; opcionalmente criar evidencia de manutencao. |

## Estrategica

| Pergunta | Gatilho de acao | Acao sugerida | Evidencia esperada |
|---|---|---|---|
| Q-EST-001 — plano estruturado de transicao | Nao/parcial | Formalizar plano-mestre da Reforma com fases, responsaveis, riscos e cadencia de comite. | Plano aprovado pela diretoria. |
| Q-EST-002 — impacto em creditos, debitos, resultado e precos | Nao/parcial | Executar workshop fiscal-contabil-financeiro para mapear efeitos em margem, preco e credito. | Ata, matriz de impacto e premissas. |
| Q-EST-003 — margens e precos por destino/regiao | Nao/parcial | Simular politica de precos por UF/canal considerando tributacao no destino. | Planilha de cenarios e decisao comercial. |
| Q-EST-004 — contratos revisados | Nao/parcial | Revisar contratos com clausulas de repactuacao, gross-up e matriz de responsabilidades fiscais. | Minuta padrao e lista de contratos criticos. |

## Tecnologica

| Pergunta | Gatilho de acao | Acao sugerida | Evidencia esperada |
|---|---|---|---|
| Q-TEC-001 — ERP adaptado para IBS/CBS | Nao/parcial | Mapear lacunas do ERP e abrir roadmap com fornecedor/modulo fiscal. | Backlog tecnico priorizado. |
| Q-TEC-002 — cClassTrib, cCredPres e NT 2025.002 | Nao/parcial | Homologar campos fiscais novos em NF-e/NFC-e/NFS-e e validar XMLs de teste. | Massa de testes e XMLs validados. |
| Q-TEC-003 — split payment/retencoes | Nao/parcial | Avaliar impacto de recolhimento, conciliacao bancaria e integracoes financeiras. | Desenho de processo financeiro futuro. |
| Q-TEC-004 — monitoramento de NTs | Nao/parcial | Criar rotina mensal de monitoramento normativo e tecnico com dono definido. | Calendario, fontes monitoradas e registro de decisoes. |

## Fiscal

| Pergunta | Gatilho de acao | Acao sugerida | Evidencia esperada |
|---|---|---|---|
| Q-FISC-001 — beneficios e regimes especiais ate 2033 | Nao/parcial | Inventariar beneficios e regimes especiais, com data de fim/alteracao e impacto. | Inventario de beneficios por operacao. |
| Q-FISC-002 — extincao de regimes especiais | Nao/parcial | Avaliar Reporto, Recap, creditos presumidos e outros regimes no modelo de transicao. | Parecer interno e matriz de risco. |
| Q-FISC-003 — creditos acumulados ICMS/PIS/COFINS | Nao/parcial | Criar controle de creditos acumulados e plano de utilizacao/ressarcimento. | Razao auxiliar de creditos e reconciliacao. |
| Q-FISC-004 — Imposto Seletivo no mix | Nao/parcial | Classificar mix sujeito a IS e estimar impacto em preco/margem. | Relatorio por NCM/produto. |
| Q-VAREJO-001 — varejo/atacado margem e precificacao | Nao/parcial | Recalcular margem por categoria e canal, com foco em credito/debito. | DRE por categoria. |
| Q-VAREJO-002 — alto volume de ICMS-ST | Nao/parcial | Mapear SKUs/UFs com ICMS-ST e simular fim/alteracao do regime. | Lista de SKUs ST e simulacao de capital de giro. |
| Q-VAREJO-003 — cesta basica/aliquota reduzida | Nao/parcial | Identificar produtos com reducao, isencao ou tratamento diferenciado. | Tabela de produtos elegiveis e base legal. |
| Q-IND-001 — cadeia industrial e destino | Nao/parcial | Simular cadeia fornecedores-CD-filiais-clientes sob tributacao no destino. | Mapa da cadeia e cenarios por UF. |
| Q-IND-002 — extincao do IPI exceto ZFM | Nao/parcial | Avaliar mix industrial afetado por IPI/ZFM e reflexos na precificacao. | Relatorio por NCM/familia. |
| Q-IND-003 — CBS em insumos, energia e creditos | Nao/parcial | Recalcular creditamento de insumos/energia e efeitos em custo industrial. | Memoria de calculo por centro de custo. |
| Q-SERV-001 — NFS-e layout RTC | Nao/parcial | Homologar emissao NFS-e conforme NTs CGNFS-e. | XML/JSON de teste e aceite tecnico. |
| Q-SERV-002 — aliquota IBS+CBS sobre servicos | Nao/parcial | Simular margem por tipo de servico e repasse contratual. | Matriz de contratos e precos. |
| Q-SERV-003 — setores com aliquota diferenciada | Nao/parcial | Confirmar enquadramento em saude, educacao, transporte ou outro regime favorecido. | Parecer de enquadramento. |
| Q-AGRO-001 — reducao de aliquota agro | Nao/parcial | Mapear produtos agropecuarios elegiveis a reducao e impacto em margem. | Tabela produto x tratamento. |
| Q-AGRO-002 — credito presumido produtor rural PF | Nao/parcial | Avaliar apropriacao de credito presumido por agroindustria/cooperativa. | Politica de creditamento e controles. |

## Financeira

| Pergunta | Gatilho de acao | Acao sugerida | Evidencia esperada |
|---|---|---|---|
| Q-FIN-001 — estoques e reposicao | Nao/parcial | Simular giro de estoque e risco de perda de creditos na transicao. | Curva ABC e plano de reposicao. |
| Q-REAL-003 — fluxo de caixa 2026-2033 | Nao/parcial | Criar modelo de fluxo de caixa por cenario de aliquota e prazo de recuperacao de creditos. | Modelo financeiro versionado. |

## Operacional

| Pergunta | Gatilho de acao | Acao sugerida | Evidencia esperada |
|---|---|---|---|
| Q-OPER-001 — rastreio de creditos entre compras/vendas/servicos | Nao/parcial | Documentar processo ponta a ponta de credito tributario e pontos de controle. | POP e matriz RACI. |
| Q-OPER-002 — operacoes entre filiais/fornecedores/clientes | Nao/parcial | Simular operacoes intercompany e logistica sob tributacao no destino. | Mapa de fluxos e impactos. |
| Q-OPER-003 — treinamentos IBS/CBS/IS | Nao/parcial | Montar trilha de capacitacao para fiscal, contabilidade, comercial, TI e compras. | Plano de treinamento e lista de presenca. |

## Contabil

| Pergunta | Gatilho de acao | Acao sugerida | Evidencia esperada |
|---|---|---|---|
| Q-REAL-001 — reestruturacoes societarias | Nao/parcial | Avaliar filiais, holdings, M&A e reorganizacoes frente a impactos fiscais. | Memorando societario-fiscal. |
| Q-REAL-002 — substituto tributario no modelo CBS/IBS | Nao/parcial | Definir controles de substituicao tributaria futura e conciliacao. | Desenho de controle e evidencias. |
| Q-REAL-004 — impactos em IRPJ/CSLL | Nao/parcial | Avaliar reflexos contabeis e fiscais indiretos em IRPJ/CSLL. | Nota tecnica contabil. |
| Q-REAL-005 — clausulas de repactuacao em contratos longos | Nao/parcial | Criar governanca contratual para contratos acima de 12 meses. | Politica de contratos longos. |

## Compliance ABNT NBR 17301

| Pergunta | Gatilho de acao | Acao sugerida | Evidencia esperada |
|---|---|---|---|
| Q-ABNT-001 — politica formal | Escala 1-3 | Redigir, aprovar e divulgar politica de compliance tributario. | Politica assinada e comunicacao interna. |
| Q-ABNT-002 — riscos fiscais periodicos | Escala 1-3 | Implantar matriz de riscos fiscais com revisao periodica. | Matriz de riscos e ata de revisao. |
| Q-ABNT-003 — controles documentados | Escala 1-3 | Documentar ITs, fluxos e controles de obrigacoes tributarias. | Biblioteca de ITs e controles. |
| Q-ABNT-004 — monitoramento continuo | Escala 1-3 | Implantar monitoramento mensal de obrigacoes, incidentes e indicadores. | Painel de indicadores e registros. |
| Q-ABNT-005 — melhoria continua | Escala 1-3 | Implantar ciclo PDCA para nao conformidades e melhorias tributarias. | Registro de acao corretiva e licoes aprendidas. |

