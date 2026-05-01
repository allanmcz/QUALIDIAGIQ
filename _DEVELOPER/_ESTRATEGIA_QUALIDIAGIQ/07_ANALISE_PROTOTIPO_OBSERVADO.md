# 07 — Análise de Viabilidade do Protótipo Observado

> **Análise feita em 2026-04-26** sobre protótipo de diagnóstico apresentado pelo Allan em 14 telas (1 captura de perfil + 13 perguntas Sim/Parcial/Não + 1 pergunta condicional varejo).
> **Conclusão:** **Viável** como base do QDI Free 1.0, com **3 ajustes obrigatórios** antes do go-live.

---

## 1. Resposta Direta

O protótipo é tecnicamente trivial de implementar e tem **UX moderna e profissional** (dark theme + gradiente + barra de progresso + captura de perfil rica). Pode virar o **MVP do QDI Free** com **6-7 perguntas adicionais** e ajustes pontuais. Os **3 gaps críticos** são: (a) zero perguntas ABNT NBR 17301 — perde diferencial #1; (b) adaptatividade fraca (apenas 1 pergunta condicional); (c) resposta ternária limita granularidade do score.

## 2. Inventário do Protótipo (14 perguntas)

| # | Pergunta resumida | Dimensão Primária |
|---|-------------------|-------------------|
| 1 | Plano estruturado de transição | Estratégica |
| 2 | ERP adaptado IBS/CBS | Tecnológica |
| 3 | Modelo créditos/débitos no resultado e preço | Estratégica |
| 4 | Benefícios fiscais/regimes especiais até 2033 | Fiscal |
| 5 | Forma de recolhimento (split payment) | Financeira |
| 6 | Rastreamento de créditos compras/vendas | Contábil |
| 7 | Operações entre filiais (tributação destino) | Operacional |
| 8 | Contratos comerciais revisados | Operacional |
| 9 | Treinamentos internos IBS/CBS/IS | Operacional |
| 10 | Margens e políticas de preço por região | Estratégica |
| 11 | Gestão de estoques (créditos transição) | Contábil |
| 12 | Extinção de regimes especiais (Reporto, Recap) | Fiscal |
| 13 | Créditos ICMS/PIS/COFINS acumulados | Fiscal |
| 14 | Varejo — créditos/débitos na margem | Estratégica (setorial) |

## 3. Forças do Design

- UX dark theme + gradiente cyan→magenta (profissional, executiva)
- Barra de progresso em % visível (reduz drop-off)
- 3 opções padronizadas (Sim/Parcial/Não) — velocidade
- Captura de perfil rica antes do questionário (regime + segmento + setor)
- Wizard linear simples (funciona em desktop e mobile)
- "Anterior" disponível em todas as telas
- Última pergunta adaptativa por setor (pergunta 14 — varejo)
- Linguagem técnica acessível ("split payment", "tributação no destino")
- Sem captura de e-mail no início (alinhado com estratégia)
- Citação da metodologia ("diretrizes oficiais da Reforma")

## 4. Gaps Críticos

### 4.1. 🔴 Zero perguntas ABNT NBR 17301
Diferencial #1 do QDI fica sem cobertura. Sem isso, produto vira "mais um Cosmos".

### 4.2. ⚠️ Adaptatividade fraca
Apenas 1 pergunta condicional (a 14ª). Outras 13 iguais para todos.

### 4.3. ⚠️ Resposta ternária
Sim=100, Parcial=50, Não=0 → score com baixa granularidade. Sem nuance entre "iniciado raso" e "iniciado robusto".

### 4.4. ⚠️ Cobertura tecnológica rasa
Apenas 2 perguntas tecnológicas. Faltam cClassTrib + NFS-e RTC.

### 4.5. ⚠️ Sobrecarga estratégica
6 perguntas (43%) caem em "Estratégica" — score dessa dimensão fica superdeterminado.

## 5. Roadmap de Evolução (14 → 21 perguntas)

### 5.1. Adicionar 5 perguntas ABNT NBR 17301 (Bloco 5)

| Nova # | Pergunta | Eixo PDCA |
|--------|----------|-----------|
| 15 | Política interna formal de Compliance Tributário? | Plan |
| 16 | Identificação periódica de riscos fiscais? | Plan + Check |
| 17 | Controles operacionais documentados e auditáveis? | Do |
| 18 | Monitoramento contínuo das obrigações? | Check |
| 19 | Mecanismo formal de melhoria contínua? | Act |

### 5.2. Adicionar 2 perguntas tecnológicas críticas

| Nova # | Pergunta |
|--------|----------|
| 20 | Sistema pronto para cClassTrib + cCredPres? |
| 21 | NFS-e adequada ao layout RTC (condicional: serviços)? |

### 5.3. Reclassificar 2 perguntas

- Pergunta 7 (filiais) → reclassificar para Operacional principal (era Estratégica)
- Pergunta 8 (contratos) → reclassificar para Estratégica principal (era Operacional)

### 5.4. Distribuição final equilibrada

| Dimensão | Perguntas | % | Avaliação |
|----------|-----------|---|-----------|
| Fiscal | 4, 12, 13 | 14% | ✅ |
| Estratégica | 1, 3, 8, 10 | 19% | ✅ |
| Contábil | 6, 11 | 10% | ✅ |
| Financeira | 5 | 5% | ✅ |
| Operacional | 7, 9 | 10% | ✅ |
| Tecnológica | 2, 20, 21 | 14% | ✅ |
| **Compliance ABNT** | 15, 16, 17, 18, 19 | **24%** | ✅ Diferencial |
| Varejo (cond.) | 14 | 5% | ✅ |
| **Total** | **21 perguntas** | **100%** | ✅ |

## 6. Estimativa de Implementação

| Tarefa | Tempo |
|--------|-------|
| Migrar design para Next.js + Tailwind + shadcn/ui | 12h |
| Implementar wizard adaptativo (condicionais) | 8h |
| Adicionar 7 perguntas (5 ABNT + 2 tech) com pesos | 4h |
| Motor de score 0-100 ponderado | 6h |
| Tela de resultado + PDF (WeasyPrint) | 10h |
| Captura de e-mail + envio | 4h |
| Testes + ajustes | 6h |
| **Total** | **~50h = ~3 semanas a 3h/dia** |

## 7. Recomendações Operacionais

### 7.1. Adotar como base
**Sim, adotar este design como base do QDI Free 1.0** — supera concorrentes em UX e captura.

### 7.2. Ajustes obrigatórios antes do go-live

1. **Adicionar 5 perguntas ABNT NBR 17301** (item 5.1) — recupera diferencial #1
2. **Adicionar 2 perguntas tecnológicas** (cClassTrib + NFS-e) — alinha com TABELAS_TRIBUTARIAS
3. **Reclassificar dimensões** das 2 perguntas redistribuíveis

### 7.3. Ajustes recomendados (não bloqueantes)

- Adicionar tooltips educativos em termos técnicos
- Adicionar header "Bloco X/7 — Nome da Dimensão" para contextualizar
- Usar escala 1-5 em 4-5 perguntas críticas ABNT (granularidade)
- Adicionar mais condicionais por setor (3-5 perguntas em vez de 1)

### 7.4. Triggers de upgrade Free → Plus

Após implementação, integrar gatilhos contextuais (vide `03_EVOLUCAO_PAGA.md`):
- Resposta "Não" em Q-20 (cClassTrib) → "Plus calcula impacto em R$"
- Resposta "Parcialmente" em Q-15-19 (ABNT) → "Pré-auditoria completa no Pro"
- Score ABNT < 40 → "Sua empresa precisa do QDI Pro com pré-auditoria ABNT"

## 8. Decisão Recomendada

**Aprovar o protótipo como base do QDI Free 1.0**, com escopo MVP estendido para 21 perguntas (não 14). Cabe em 3 semanas do Sprint 1 a 3h/dia. Próximo passo: redigir ADR-009 com pesos finais e iniciar implementação no scaffold `018-QUALIDIAGIQ/`.
