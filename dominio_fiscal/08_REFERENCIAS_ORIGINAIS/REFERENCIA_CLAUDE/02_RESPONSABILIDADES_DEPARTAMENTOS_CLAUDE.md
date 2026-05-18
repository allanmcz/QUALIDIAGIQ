# MATRIZ DE RESPONSABILIDADES POR DEPARTAMENTO

**Documento:** 02 — Responsabilidades RACI por área envolvida no CIRT
**Setor de aplicação:** Varejo / Atacarejo / Atacado
**Versão:** 1.0

---

## Bloco A — Resumo Executivo

Este documento descreve, departamento por departamento, as **responsabilidades operacionais e de governança** no projeto de adequação à Reforma Tributária. A matriz adota a notação **RACI**:

- **R** (Responsible) — quem executa
- **A** (Accountable) — quem responde formalmente pelo resultado
- **C** (Consulted) — quem deve ser consultado antes da decisão
- **I** (Informed) — quem deve ser informado após a decisão

Cada departamento tem **tarefas próprias indelegáveis** e **pontos de interface obrigatórios** com outras áreas. A leitura conjunta com o Documento 01 (Pauta) e o Documento 04 (Checklist) é essencial.

---

## Bloco B — Diretoria Financeira / Sponsor (CFO)

### Papel no comitê
Sponsor formal, com autoridade decisória final e responsabilidade institucional perante o Conselho de Administração ou Diretoria-Geral.

### Responsabilidades específicas
- Aprovar o cronograma e o orçamento do projeto.
- Indicar o coordenador-executivo.
- Aprovar contratações de consultoria externa, sistemas e treinamentos.
- Mediar conflitos interdepartamentais.
- Reportar mensalmente à alta administração os marcos e riscos.
- Assinar e validar pareceres de impacto financeiro.

### Pontos de atenção
- Não tratar a reforma como tema exclusivamente fiscal — é tema **estratégico e financeiro**.
- Garantir que o caixa do período de transição contemple os impactos de creditamento postergado e ressarcimento de saldos credores.

---

## Bloco C — Departamento Fiscal / Tributário

### Papel no comitê
**Coordenador-executivo do CIRT**. Núcleo técnico do projeto.

### Responsabilidades específicas
- Coordenar a interpretação normativa.
- Manter o repositório legal atualizado (LCP 214/2025, Notas Técnicas, IT 2024.001, IT 2025.002).
- Liderar a reclassificação fiscal de produtos (cClassTrib, CST de IBS/CBS, NCM, NBS).
- Apurar IBS, CBS e Imposto Seletivo no período de transição e em regime pleno.
- Validar parametrizações em ERP com TI.
- Gerenciar a transição de PIS/COFINS, ICMS e ISS (extinção, saldos credores, ressarcimento).
- Acompanhar consultas, soluções de divergência e regulamentação infralegal do Comitê Gestor do IBS.
- Conduzir treinamentos técnicos internos.

### Interfaces obrigatórias
- TI (parametrização ERP)
- Contabilidade (refletir tributos na DRE e no Balanço)
- Compras (CFOP, cadastro de fornecedores, crédito)
- Comercial (precificação, NF-e de venda)
- Jurídico (contratos e contencioso)

### Risco principal
Reclassificação incorreta de cClassTrib ou CST → emissão de NF-e rejeitada, crédito não tomado pelo cliente, perda de competitividade.

---

## Bloco D — Departamento Contábil / Controladoria

### Papel no comitê
Tradução dos efeitos da reforma para contas contábeis, DRE, balanço, gestão de saldos credores e variação de margem.

### Responsabilidades específicas
- Mapear o plano de contas atual e propor ajustes para o novo modelo.
- Refletir contabilmente a apuração paralela 2026-2032.
- Tratar os saldos credores de PIS/COFINS na transição (registro, atualização monetária quando aplicável, baixa).
- Recalcular margem de contribuição produto a produto após a reforma.
- Apoiar a Diretoria com simulações de impacto financeiro.
- Validar relatórios gerenciais e KPIs sob nova base tributária.

### Interfaces obrigatórias
- Fiscal (matriz de cClassTrib e regime aplicável)
- TI (parâmetros do ERP financeiro/contábil)
- Comercial (margem por produto e por canal)

### Risco principal
Manutenção de práticas contábeis legadas que ocultem o real impacto financeiro da reforma → decisão estratégica baseada em DRE descalibrada.

---

## Bloco E — Tecnologia da Informação (ERP e Sistemas)

### Papel no comitê
Sustentação tecnológica do projeto.

### Responsabilidades específicas
- Levantar versão atual do ERP (Winthor, Protheus, SAP, TOTVS, outros) e plano de roadmap do fornecedor para a reforma.
- Validar a aderência do ERP à NT 2025.002 (campos de IBS, CBS, IS na NF-e).
- Implementar e testar as tabelas oficiais: cClassTrib, cCredPres, CST de IBS/CBS, NCM atualizada, NBS, Tabela CFOP.
- Disponibilizar ambiente de homologação para testes integrados.
- Gerenciar integrações com SEFAZ, RFB, Comitê Gestor do IBS, emissores de NF-e/NFC-e/NFCom/NFS-e.
- Manter trilha de auditoria de parametrizações.
- Garantir backup, versionamento e governança de mudança (change management).
- Apoiar o Fiscal nos testes do ambiente beta da RTC.

### Interfaces obrigatórias
- Fiscal (regras tributárias)
- Compras e Comercial (cadastro de fornecedores e clientes)
- Controladoria (relatórios gerenciais)

### Risco principal
Atraso de roadmap do fornecedor de ERP ou customização inadequada → impossibilidade de emitir NF-e com campos obrigatórios da NT 2025.002 → paralisação operacional.

---

## Bloco F — Compras / Suprimentos

### Papel no comitê
Garantir que a cadeia de fornecedores esteja apta a emitir documentos fiscais conforme o novo padrão e que os créditos sejam corretamente apropriados.

### Responsabilidades específicas
- Revisar cadastro de fornecedores: CNPJ, regime tributário, situação de cClassTrib aplicada.
- Avaliar a capacidade técnica do fornecedor para emitir NF-e adequada à NT 2025.002.
- Renegociar contratos de fornecimento que prevejam cláusulas tributárias defasadas.
- Atualizar instrumentos de cotação para considerar crédito amplo (neutralidade).
- Mapear bens de uso e consumo e definir tratamento conforme LCP 124/2025.
- Acompanhar saldo credor histórico de PIS/COFINS atribuível à área.

### Interfaces obrigatórias
- Fiscal (regra de crédito, regime)
- Comercial (impacto de preço de venda derivado de mudança de custo)
- Jurídico (contratos)

### Risco principal
Aceitar NF-e de fornecedor incorreta → glosa de crédito de IBS/CBS → impacto direto no caixa.

---

## Bloco G — Comercial / Pricing / Marketing

### Papel no comitê
Repactuação da política de preços, comunicação ao cliente B2B e B2C, e revisão da rentabilidade por canal.

### Responsabilidades específicas
- Recalcular preços de venda **por SKU e por canal** considerando o novo modelo (crédito amplo, fim do efeito-cascata).
- Avaliar a oportunidade competitiva da neutralidade plena versus a captura de margem.
- Revisar tabelas, listas de preço, contratos comerciais e políticas de desconto.
- Comunicar formalmente clientes B2B sobre a nova sistemática de creditamento.
- Adequar materiais de campanha e ações promocionais.
- Avaliar o impacto do Imposto Seletivo em itens específicos (quando aplicáveis ao mix).

### Interfaces obrigatórias
- Fiscal (regra tributária por produto)
- Controladoria (margem)
- Marketing (comunicação)
- Jurídico (revisão contratual)

### Risco principal
Manutenção de preços calculados na lógica antiga (cumulativa) → perda de margem em produtos com crédito amplo ou perda de competitividade em produtos sob regime específico.

---

## Bloco H — Jurídico / Compliance

### Papel no comitê
Análise normativa, contencioso, contratual e regulatória.

### Responsabilidades específicas
- Acompanhar regulamentação infralegal e jurisprudência.
- Revisar contratos de compra, venda, locação, terceirização e fornecimento de serviços.
- Avaliar contratos de longo prazo: rebalanceamento, repactuação, cláusulas de revisão.
- Apoiar o Fiscal em consultas formais a fiscos.
- Gerir contencioso ativo de PIS/COFINS, ICMS e ISS no período de transição.
- Avaliar oportunidades de planejamento legítimo.
- Atuar em comunicação institucional sobre temas regulatórios.

### Interfaces obrigatórias
- Fiscal (interpretação tributária)
- Compras e Comercial (contratos)
- Diretoria (decisões estratégicas)

### Risco principal
Manter contratos rígidos sem cláusulas de revisão tributária → perda de margem ou repasse indevido ao cliente.

---

## Bloco I — Operações / Logística

### Papel no comitê
Adequar processos físicos e documentais às novas regras de circulação de mercadorias.

### Responsabilidades específicas
- Revisar fluxos de transferência entre filiais (com novo tratamento dado pela LCP 214/2025).
- Adequar operações de devolução, bonificação, remessa para industrialização, conserto, demonstração e amostra.
- Validar processos de recebimento de mercadorias com a nova NF-e.
- Adaptar processos de logística reversa.
- Avaliar impacto na frota e em contratos de logística terceirizada (uso de NFCom etc.).

### Interfaces obrigatórias
- Fiscal (CFOP, cClassTrib)
- TI (integração WMS / TMS)
- Compras (cadastro)

### Risco principal
Falha em mapear operações híbridas → NF-e incorreta, autuação fiscal, glosa de crédito.

---

## Bloco J — Recursos Humanos

### Papel no comitê
Capacitação e gestão da mudança.

### Responsabilidades específicas
- Estruturar o **Plano de Capacitação Interna** (ver Documento 03).
- Mobilizar instrutores internos e externos.
- Avaliar impacto na folha (caso a empresa tenha autônomos, terceiros sob CBS, prestadores etc.).
- Liderar a **gestão da mudança** (comunicação interna, engajamento, cultura).
- Apoiar o Comitê na avaliação de competências técnicas necessárias.

### Interfaces obrigatórias
- Fiscal (conteúdo técnico das capacitações)
- Diretoria (patrocínio)
- Comunicação Interna (campanhas)

### Risco principal
Subestimar a necessidade de qualificação → equipe sem competência técnica para operar o novo modelo → erro sistemático em apuração e emissão.

---

## Bloco K — Auditoria Interna / Controles Internos

### Papel no comitê
Validação independente da qualidade de controles e de conformidade.

### Responsabilidades específicas
- Auditar a matriz de parametrização do ERP.
- Verificar trilha de evidências (resoluções, atas, documentos legais).
- Testar a aderência do processo à regulamentação.
- Reportar achados à Diretoria.
- Acompanhar o atendimento a recomendações.

### Interfaces obrigatórias
- Todos os departamentos (papel de auditoria horizontal).

### Risco principal
Comitê operar sem auditoria → projeto sem governança de conformidade → exposição a autuações.

---

## Bloco L — Matriz RACI Consolidada (visão por entregável)

| Entregável-chave | Fiscal | Contábil | TI | Compras | Comercial | Jurídico | Operações | RH | Sponsor |
|------------------|--------|----------|-----|---------|-----------|----------|-----------|-----|---------|
| Mapa normativo | **A/R** | C | I | I | I | C | I | I | I |
| Reclassificação fiscal de SKUs | **A/R** | C | R | C | C | I | I | I | I |
| Parametrização do ERP | A | C | **A/R** | C | C | I | C | I | I |
| Revisão de contratos | C | I | I | C | C | **A/R** | C | I | I |
| Política de precificação | C | C | I | I | **A/R** | C | I | I | A |
| Plano de capacitação | C | I | I | I | I | I | I | **A/R** | A |
| Conciliação contábil | C | **A/R** | C | I | I | I | I | I | I |
| Testes em ambiente beta da RTC | A | C | **R** | I | I | I | C | I | I |
| Reporte ao Conselho | C | C | I | I | I | I | I | I | **A/R** |
| Auditoria de conformidade | C | C | C | C | C | C | C | C | **A** |

> A célula em negrito indica o **Accountable**; demais R/C/I indicam Responsibles, Consulted e Informed.

---

## Bloco M — Exemplo Prático Aplicado ao Varejo

**Cenário:** Cadeia de atacarejo com 25 mil SKUs, presente em 3 estados, emitente de NF-e e NFC-e.

**Distribuição prática das atividades nos primeiros 90 dias:**

| Semana | Fiscal | TI | Compras | Comercial | Jurídico | RH |
|--------|--------|-----|---------|-----------|----------|-----|
| 1-2 | Estudo da LCP 214/2025 | Levantar versão do ERP | Mapear top-50 fornecedores | Identificar top-100 SKUs por margem | Mapear contratos críticos | Estruturar trilha de capacitação |
| 3-4 | Classificar cClassTrib dos primeiros 5.000 SKUs | Solicitar roadmap ao fornecedor do ERP | Pesquisar adequação de fornecedores | Iniciar simulação de preço dos top-100 | Revisar contratos de fornecimento | Iniciar treinamentos básicos |
| 5-8 | Concluir matriz IBS/CBS de 100% dos SKUs | Configurar ambiente de homologação | Renegociar contratos | Estender simulação aos demais SKUs | Concluir revisão contratual | Avançar treinamento técnico |
| 9-12 | Validar com TI | Executar primeira bateria de testes | Validar cadastro de fornecedores | Aprovar política de preço de transição | Emitir parecer consolidado | Treinamento avançado para Fiscal e TI |

**Resultado esperado em 90 dias:**
- 100% dos SKUs reclassificados e validados.
- ERP em ambiente de homologação aderente à NT 2025.002.
- Cadastro de fornecedores tratados conforme regime.
- Política de preço de transição aprovada.
- Contratos críticos revisados.
- Equipe técnica capacitada nos temas essenciais.

---

## Bloco N — Conclusão Objetiva

A reforma tributária é, no fundo, um **projeto interdepartamental de governança**. O sucesso depende menos de domínio técnico fiscal isolado e mais da capacidade de **orquestrar áreas, dados, sistemas e pessoas** sob um cronograma firme. A matriz RACI aqui proposta deve ser **revisada na primeira reunião do CIRT e formalmente aprovada como anexo à resolução de constituição**.

---

*Recomendação: vincular esta matriz ao sistema de gestão (PMO, ERP de projeto ou planilha de governança) para acompanhamento semanal.*
