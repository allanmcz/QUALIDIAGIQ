# 05 — Banco de Perguntas e Dimensões

## 1. Resposta Direta

Este documento materializa o **banco inicial de ~40 perguntas** organizadas pelas **7 dimensões** do QDI (Fiscal, Estratégica, Contábil, Financeira, Operacional, Tecnológica, Compliance ABNT 17301). Cada pergunta tem **peso explícito**, **condicionais** (segmento+regime+porte+UF), **tipo de resposta** e **base legal citada**. Essas ~40 perguntas são o **MVP do questionário**; em ondas posteriores podem chegar a 80-100 (sem aumentar tempo de execução, graças à adaptatividade).

## 2. Estrutura de Cada Pergunta

```yaml
codigo: Q-XXX-NNN  # X = dimensão, NNN = sequencial
texto: "Pergunta clara em PT-BR"
dimensao: FISCAL | ESTRATEGICA | CONTABIL | FINANCEIRA | OPERACIONAL | TECNOLOGICA | COMPLIANCE_ABNT
tipo: BINARIA | ESCALA_1_5 | MULTIPLA_ESCOLHA | NUMERICA | CHECKLIST
peso: 0.0–10.0   # quanto vale na composição do score da dimensão
condicional:
  segmento: [...]
  regime: [...]
  porte_minimo: ...
  uf: [...]
base_legal: "LC X art. Y; EC Z; NT N"
ajuda: "Texto curto explicando termo técnico ao usuário"
upsell_plus: "O que o Plus faria diferente nessa pergunta"
```

## 3. Distribuição das Perguntas

| Dimensão | Núcleo (todos) | Condicionais | Total |
|----------|----------------|--------------|-------|
| Fiscal | 4 | +4 (por segmento+regime) | 4-8 |
| Estratégica | 3 | +1 (Lucro Real) | 3-4 |
| Contábil | 3 | +1 (Lucro Real ou Presumido) | 3-4 |
| Financeira | 3 | +1 (Médio+) | 3-4 |
| Operacional | 3 | +1 (Indústria/Comércio) | 3-4 |
| Tecnológica | 4 | +1 (Médio+) | 4-5 |
| Compliance ABNT | 5 | 0 | 5 |
| **Total** | **25** | **+8 condicionais** | **25-34** |

Para um cliente típico: **~25 perguntas respondidas em 10-12 minutos**.

## 4. Banco de Perguntas — Núcleo do MVP

### 4.1. Dimensão Fiscal (peso de dimensão = 1.5)

#### Q-FISC-001 — Mapeamento de impactos
```yaml
texto: "Sua empresa já mapeou o impacto do fim do ICMS-ST no seu mix de produtos?"
tipo: ESCALA_1_5
peso: 8.5
base_legal: "EC 132/2023; LC 214/2025"
ajuda: "ICMS-ST (Substituição Tributária) deixa de existir nos moldes atuais; mapeamento identifica produtos afetados"
upsell_plus: "Plus calcula a recuperação de ST em estoque na transição em R$ exato"
```

#### Q-FISC-002 — Apuração CBS/IBS
```yaml
texto: "Sua empresa já realizou simulações de apuração CBS+IBS para 2027 com sua receita atual?"
tipo: BINARIA
peso: 9.0
base_legal: "LC 214/2025 art. 12-15"
ajuda: "CBS substitui PIS/COFINS; IBS substitui ICMS+ISS; ambos não-cumulativos"
upsell_plus: "Plus simula 3 cenários (otimista/realista/pessimista) por categoria"
```

#### Q-FISC-003 — Créditos acumulados
```yaml
texto: "Sua empresa tem créditos de PIS/COFINS acumulados que poderiam ser recuperados antes da CBS?"
tipo: ESCALA_1_5
peso: 7.5
base_legal: "Lei 10.637/02; Lei 10.833/03; LC 214/2025 art. 130"
upsell_plus: "Plus estima R$ recuperáveis por ano com base em DCTF"
```

#### Q-FISC-004 — Regimes especiais
```yaml
texto: "Sua empresa utiliza regimes especiais (Lei do Bem, REINTEGRA, regimes setoriais)?"
tipo: CHECKLIST
peso: 6.5
base_legal: "Lei 11.196/05; Lei 13.043/14; LC 214/2025 art. 145"
ajuda: "Regimes especiais terão tratamento específico na transição"
```

#### Q-FISC-005 — ICMS-ST específico (condicional segmento=COMERCIO)
```yaml
texto: "Qual percentual do seu faturamento atual está sob ICMS-ST?"
tipo: NUMERICA
peso: 8.0
condicional:
  segmento: [COMERCIO]
base_legal: "Convênios ICMS; LC 214/2025 art. 415"
upsell_plus: "Plus calcula impacto no capital de giro com fim do ST"
```

#### Q-FISC-006 — Imposto Seletivo (condicional setor)
```yaml
texto: "Sua empresa comercializa produtos sujeitos a Imposto Seletivo (combustíveis, bebidas alcoólicas, fumo, veículos)?"
tipo: BINARIA
peso: 7.0
condicional:
  setor_macro: [COMERCIO, INDUSTRIA, AGRO]
base_legal: "EC 132/2023 art. 153, VIII; LC 214/2025 art. 432"
```

#### Q-FISC-007 — Regimes diferenciados (LC 214 — saúde, educação, agro)
```yaml
texto: "Sua empresa atua em setor com alíquota reduzida (saúde, educação, agro, transporte coletivo, cesta básica)?"
tipo: BINARIA
peso: 7.0
base_legal: "LC 214/2025 art. 9º (cesta básica); art. 137 (saúde); art. 145 (educação)"
```

#### Q-FISC-008 — Substituição Tributária CBS/IBS (Lucro Real)
```yaml
texto: "Sua empresa atua como substituto tributário no novo modelo CBS/IBS?"
tipo: BINARIA
peso: 6.5
condicional:
  regime: [LUCRO_REAL]
base_legal: "LC 214/2025 art. 60-65"
```

---

### 4.2. Dimensão Estratégica (peso de dimensão = 1.0)

#### Q-EST-001 — Política de pricing
```yaml
texto: "Sua empresa já recalculou margens considerando a alíquota combinada CBS+IBS?"
tipo: ESCALA_1_5
peso: 7.5
base_legal: "Pesquisa PwC (37% empresas revisam mix)"
upsell_plus: "Plus calcula margem nova por SKU"
```

#### Q-EST-002 — Mix de produtos
```yaml
texto: "Sua empresa avaliou se o mix atual de produtos/serviços continua sendo competitivo no novo regime?"
tipo: ESCALA_1_5
peso: 7.0
ajuda: "Alguns produtos podem deixar de ser rentáveis; outros ganham margem"
```

#### Q-EST-003 — Cadeia logística
```yaml
texto: "Sua empresa avaliou impactos no posicionamento de Centros de Distribuição com a tributação no destino?"
tipo: ESCALA_1_5
peso: 7.5
base_legal: "LC 214/2025 art. 5º (destino)"
ajuda: "Fim da guerra fiscal altera atratividade de incentivos estaduais"
```

#### Q-EST-004 — Reestruturação societária (condicional Real)
```yaml
texto: "Sua empresa avaliou reestruturações societárias (filiais, holding, fusões) à luz da Reforma?"
tipo: BINARIA
peso: 6.5
condicional:
  regime: [LUCRO_REAL]
base_legal: "Pesquisa PwC (31% empresas avaliam reestruturação)"
```

---

### 4.3. Dimensão Contábil (peso de dimensão = 1.0)

#### Q-CONT-001 — Plano de contas
```yaml
texto: "Seu plano de contas atual está preparado para receber as contas de CBS, IBS e Imposto Seletivo?"
tipo: ESCALA_1_5
peso: 8.0
base_legal: "ECD/ECF; ITG 2000"
ajuda: "Será necessário criar contas específicas para os novos tributos"
```

#### Q-CONT-002 — Conciliações
```yaml
texto: "Sua empresa realiza conciliação mensal entre apuração fiscal e contábil?"
tipo: ESCALA_1_5
peso: 6.5
base_legal: "ECF; CPC 32 — Tributos sobre o lucro"
```

#### Q-CONT-003 — Cadastro de itens
```yaml
texto: "Quão atualizado está o cadastro de NCM/CFOP/CEST dos seus produtos?"
tipo: ESCALA_1_5
peso: 8.5
base_legal: "Manual NF-e; NT 2025.002 (cClassTrib)"
upsell_plus: "Plus audita o catálogo via API"
```

#### Q-CONT-004 — Saldo de tributos a recolher (Real ou Presumido)
```yaml
texto: "Sua empresa tem saldo de tributos a recolher acumulado de períodos anteriores?"
tipo: BINARIA
peso: 5.5
condicional:
  regime: [LUCRO_REAL, LUCRO_PRESUMIDO]
```

---

### 4.4. Dimensão Financeira (peso de dimensão = 1.0)

#### Q-FIN-001 — Capital de giro
```yaml
texto: "Sua empresa avaliou impacto no capital de giro com a transição (split payment, fim do ST)?"
tipo: ESCALA_1_5
peso: 8.5
base_legal: "Pesquisa PwC (44% preocupação com capital de giro)"
upsell_plus: "Plus simula fluxo de caixa 2026-2033"
```

#### Q-FIN-002 — EBITDA esperado
```yaml
texto: "Você projetou impacto da Reforma sobre o EBITDA da sua empresa?"
tipo: ESCALA_1_5
peso: 7.0
base_legal: "Pesquisa PwC (20% preocupação com EBITDA)"
```

#### Q-FIN-003 — Reservas de contingência
```yaml
texto: "Sua empresa constituiu reservas para custos de adequação (sistemas, capacitação, consultoria)?"
tipo: ESCALA_1_5
peso: 6.0
```

#### Q-FIN-004 — Análise de cenários (Médio+)
```yaml
texto: "Sua empresa projeta cenários financeiros com sensibilidade a alíquotas IBS+CBS (otimista/realista/pessimista)?"
tipo: BINARIA
peso: 7.5
condicional:
  porte_minimo: MEDIO
upsell_plus: "Plus gera os 3 cenários automaticamente"
```

---

### 4.5. Dimensão Operacional (peso de dimensão = 1.0)

#### Q-OPER-001 — Equipes mobilizadas
```yaml
texto: "Quais áreas da sua empresa estão envolvidas no projeto de adequação à Reforma?"
tipo: CHECKLIST
peso: 7.0
opcoes: [Fiscal, Contábil, TI, Comercial, Jurídico, Operações, Suprimentos, Financeiro, RH]
base_legal: "Pesquisa PwC (Contabilidade 93% + TI 83%)"
```

#### Q-OPER-002 — Processos fiscais
```yaml
texto: "Os processos fiscais da empresa estão documentados (políticas, ITs, fluxos)?"
tipo: ESCALA_1_5
peso: 7.5
base_legal: "ABNT NBR 17301 — políticas internas"
```

#### Q-OPER-003 — Capacitação de equipes
```yaml
texto: "Sua empresa já iniciou plano de capacitação das equipes sobre o novo modelo CBS/IBS/IS?"
tipo: ESCALA_1_5
peso: 6.5
ajuda: "Inclui treinamento técnico para fiscal, contábil, TI"
```

#### Q-OPER-004 — Cadeia de suprimentos (Indústria/Comércio)
```yaml
texto: "Sua empresa renegociou condições com fornecedores considerando a nova tributação?"
tipo: ESCALA_1_5
peso: 6.5
condicional:
  setor_macro: [COMERCIO, INDUSTRIA]
```

---

### 4.6. Dimensão Tecnológica (peso de dimensão = 1.3)

#### Q-TEC-001 — ERP
```yaml
texto: "Seu ERP atual já recebeu ou tem roadmap de atualização para suportar CBS/IBS/IS?"
tipo: ESCALA_1_5
peso: 9.0
base_legal: "Pesquisa PwC (70% iniciaram diagnóstico ERP)"
upsell_plus: "Pro conecta direto ao seu ERP via API/CDC"
```

#### Q-TEC-002 — cClassTrib e NT 2025.002
```yaml
texto: "Seu ERP/sistema fiscal está pronto para os novos campos de NF-e (cClassTrib, cCredPres)?"
tipo: ESCALA_1_5
peso: 9.0
base_legal: "NT 2025.002; Manual NF-e"
ajuda: "cClassTrib é o código de Classificação Tributária introduzido pela Reforma"
```

#### Q-TEC-003 — Split payment
```yaml
texto: "Seu ERP/motor tributário está preparado para split payment (recolhimento simultâneo)?"
tipo: ESCALA_1_5
peso: 8.5
base_legal: "LC 214/2025 art. 200-220"
```

#### Q-TEC-004 — NFS-e Reforma
```yaml
texto: "Sua emissão de NFS-e está adequada ao novo layout RTC (CGNFS-e)?"
tipo: ESCALA_1_5
peso: 7.5
base_legal: "NT 003-007 do CGNFS-e"
condicional:
  setor_macro: [SERVICOS]
```

#### Q-TEC-005 — Integrações (Médio+)
```yaml
texto: "Sua empresa tem integrações sistêmicas com fornecedores/clientes/Bancos pré-Reforma que precisam ser adaptadas?"
tipo: ESCALA_1_5
peso: 6.5
condicional:
  porte_minimo: MEDIO
```

---

### 4.7. Dimensão Compliance ABNT NBR 17301 (peso de dimensão = 1.2)

> **5 perguntas espelham os 7 eixos da norma sob lente PDCA.**

#### Q-ABNT-001 — Política interna (Eixo 1)
```yaml
texto: "Sua empresa possui política interna formal de Compliance Tributário (escrita e aprovada)?"
tipo: ESCALA_1_5
peso: 8.5
base_legal: "ABNT NBR 17301 cap. 5.1 (Plan)"
ajuda: "Política formaliza diretrizes de governança fiscal"
```

#### Q-ABNT-002 — Identificação de riscos (Eixo 2)
```yaml
texto: "Sua empresa realiza identificação e avaliação periódica de riscos fiscais?"
tipo: ESCALA_1_5
peso: 8.5
base_legal: "ABNT NBR 17301 cap. 6.1 (Plan + Check)"
```

#### Q-ABNT-003 — Controles operacionais (Eixos 3+4)
```yaml
texto: "Os controles operacionais sobre obrigações tributárias estão documentados e auditáveis?"
tipo: ESCALA_1_5
peso: 9.0
base_legal: "ABNT NBR 17301 cap. 7.1 (Do)"
upsell_pro: "Pro gera relatório de gaps por controle"
```

#### Q-ABNT-004 — Monitoramento contínuo (Eixo 6)
```yaml
texto: "Sua empresa monitora obrigações tributárias de forma contínua (não apenas mensal/trimestral)?"
tipo: ESCALA_1_5
peso: 8.0
base_legal: "ABNT NBR 17301 cap. 9 (Check)"
```

#### Q-ABNT-005 — Programa Confia / Melhoria contínua (Eixo 7)
```yaml
texto: "Sua empresa tem mecanismo formal de melhoria contínua para o sistema tributário (revisão periódica, ações corretivas)?"
tipo: ESCALA_1_5
peso: 7.5
base_legal: "ABNT NBR 17301 cap. 10 (Act); Programa Confia da Receita Federal"
```

---

## 5. Cobertura de Compliance ABNT 17301 — Tabela Cruzada

Mapeamento das 5 perguntas para os 7 eixos da norma:

| Eixo da norma | Pergunta principal | Pergunta complementar |
|---------------|---------------------|------------------------|
| 1. Políticas internas | Q-ABNT-001 | — |
| 2. Identificação e avaliação de riscos | Q-ABNT-002 | Q-FISC-001 (mapeamento) |
| 3. Controles operacionais | Q-ABNT-003 | Q-OPER-002 (processos doc.) |
| 4. Registros | Q-ABNT-003 | Q-CONT-001 (plano de contas) |
| 5. Canais de comunicação | (a expandir em v1.1) | — |
| 6. Monitoramento contínuo | Q-ABNT-004 | Q-TEC-001 (ERP) |
| 7. Melhoria sistemática | Q-ABNT-005 | — |

**Próxima onda (v1.1):** adicionar 2 perguntas explícitas para Eixo 5 (canais de comunicação).

## 6. Estratégia de Pesos (calibração v1.0.0)

### 6.1. Hierarquia de pesos por pergunta

| Faixa de peso | Significado | Exemplos |
|----------------|-------------|----------|
| **9.0–10.0** | Crítico para Reforma | Q-FISC-002 (apuração CBS/IBS), Q-TEC-001 (ERP), Q-TEC-002 (cClassTrib), Q-ABNT-003 (controles) |
| **7.5–8.9** | Alta importância | Q-FISC-001 (mapeamento), Q-CONT-003 (cadastro), Q-FIN-001 (capital giro), Q-ABNT-001 (política), Q-ABNT-002 (riscos) |
| **6.0–7.4** | Importância média | Q-OPER-001 (equipes), Q-EST-002 (mix), Q-CONT-002 (conciliações) |
| **5.0–5.9** | Complementar | Q-CONT-004 (saldo) |

### 6.2. Pesos de dimensão

```yaml
fiscal: 1.5            # mais crítico para a Reforma
tecnologica: 1.3       # ERP é gargalo confirmado (PwC)
compliance_abnt: 1.2   # diferencial competitivo do QDI
estrategica: 1.0
contabil: 1.0
financeira: 1.0
operacional: 1.0
```

## 7. Banco de Templates de Ações (instantâneo no Free)

Para cada pergunta com gap detectado, mapeamento direto para template de ação:

| Trigger | Template de Ação | Horizonte | Criticidade |
|---------|------------------|-----------|-------------|
| Q-FISC-001 baixo | "Mapear impacto do fim do ICMS-ST no mix" | Curto | Alta |
| Q-FISC-002 baixo | "Iniciar simulação de apuração CBS+IBS" | Curto | Alta |
| Q-FISC-003 alto | "Acelerar recuperação de créditos PIS/COFINS antes da CBS" | Curto | Alta |
| Q-TEC-001 baixo | "Demandar roadmap de adequação ao fornecedor de ERP" | Curto | Alta |
| Q-TEC-002 baixo | "Solicitar atualização para suportar cClassTrib" | Curto | Alta |
| Q-ABNT-001 baixo | "Redigir Política de Compliance Tributário corporativa" | Médio | Média |
| Q-ABNT-002 baixo | "Implementar matriz de risco fiscal mensal" | Médio | Alta |
| Q-OPER-001 incompleto | "Constituir comitê multidisciplinar Reforma (mín. Fiscal+TI+Contábil)" | Curto | Alta |
| Q-EST-001 baixo | "Recalcular margens-padrão por SKU com alíquota CBS+IBS estimada" | Médio | Média |
| Q-FIN-001 baixo | "Projetar impacto no capital de giro 2026-2028" | Curto | Alta |

(O banco completo terá ~50 templates — esses 10 são os mais frequentes.)

## 8. Próximas Ondas do Banco (futuro)

| Onda | Objetivo | Quando |
|------|----------|--------|
| v1.0.0 | 25-34 perguntas (este documento) | MVP Sprint 1-3 |
| v1.1.0 | +5 perguntas Eixo 5 ABNT (comunicação) + setor saúde | Q4 2026 |
| v1.2.0 | +10 perguntas verticalização (varejo profundo, agro, saúde) | Q1 2027 |
| v2.0.0 | +20 perguntas com cases reais coletados | Q2 2027 |

## 9. Validação Externa

**Antes do GA do QDI Free**, esta lista será validada por **3 contadores externos**:

- 1 contador de escritório de pequeno porte (foco PME)
- 1 contador de empresa de grande porte (foco Lucro Real)
- 1 advogado tributarista (validação base legal)

Critério de aprovação: pelo menos 2 dos 3 dão "ok" sem ressalvas substantivas.

## 10. Próximo Passo

Ler [`06_FUNIL_E_CONVERSAO.md`](06_FUNIL_E_CONVERSAO.md) — estratégia de aquisição, canais, parcerias e métricas de conversão Free → Plus → Pro.
