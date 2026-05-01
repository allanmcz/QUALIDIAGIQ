# Fluxo do Diagnóstico, Pesos e Cálculo de Score — QualiDiagIQ
**Autor:** Antigravity (IA Pair Programmer / Arquiteto)
**Data:** 28 de Abril de 2026

Este documento sintetiza a jornada do usuário no QDI, desde o acesso até a geração do relatório, detalhando os bastidores matemáticos que garantem a transparência e auditabilidade do diagnóstico.

---

## 1. O Fluxo do Diagnóstico (Jornada End-to-End)

O diagnóstico ocorre em 8 etapas sequenciais, desenhadas para reter o usuário (fricção progressiva) e entregar valor antes de capturar dados sensíveis.

1. **Captura Inicial (30s):** Clique na landing page gera uma sessão anônima (`session_id`). Nenhum dado pessoal é exigido aqui.
2. **Perfil da Empresa (2 min):** Formulário enxuto coletando CNPJ, Razão Social, Regime Tributário, Segmento, Faturamento Estimado e UF. Crucial para as ramificações do questionário.
3. **Questionário Adaptativo (10 min):** O motor seleciona dinamicamente as perguntas (de um banco total de 35). Um cliente típico responde de 22 a 26 perguntas dependendo de seu setor (Comércio, Indústria, Agro, Serviços) e regime (Simples vs Lucro Real).
4. **Cálculo de Score (2s):** Processamento determinístico transformando as respostas em métricas (detalhado na Seção 3).
5. **Classificação e Gaps (1s):** Identificação de gargalos críticos baseados na pontuação de cada questão. Gaps recebem apontamento da base legal infringida.
6. **Plano de Ação (30s):**
   - *Free:* Determinístico, baseado em templates vinculados aos gaps.
   - *Plus:* IA Generativa (Claude Sonnet 4.6) utiliza RAG sobre a Lexiq para redigir justificativas jurídicas e táticas adaptadas à persona (CFO, Contador, etc).
7. **Captura de E-mail (30s):** Apresentação ofuscada do Score (radar parcial) com a exigência do e-mail corporativo para a liberação do resultado completo.
8. **Renderização (10s):** Geração do Dashboard Web e do Relatório PDF via WeasyPrint, disparando o e-mail com o hash do documento.

---

## 2. Sistema de Pesos e Respostas

A avaliação não é "flat". Cada Dimensão e cada Resposta têm um peso diferente, refletindo a criticidade fiscal real.

### A. Conversão de Respostas em Pontos (0 a 100)
- **Ternárias:** Sim (100) | Parcialmente (50) | Não (0)
- **Escala 1 a 5:** Nível 1 (0) | Nível 2 (25) | Nível 3 (50) | Nível 4 (75) | Nível 5 (100)

### B. Pesos das Dimensões
As dimensões não valem o mesmo. O core business da Reforma dita as prioridades:
1. **Fiscal:** 1.5 (Peso Máximo - Impacto direto de tributos e créditos)
2. **Tecnológica:** 1.3 (Risco alto de rejeição de NF-e e falha no Split Payment)
3. **Compliance ABNT 17301:** 1.2 (Diferencial exclusivo de governança)
4. **Estratégica:** 1.0
5. **Contábil:** 1.0
6. **Financeira:** 1.0
7. **Operacional:** 1.0

---

## 3. Algoritmo de Cálculo (Matemática do Score)

A totalização ocorre em duas etapas: agregação por dimensão e, em seguida, a média ponderada geral.

### Passo 1: Score por Dimensão
O sistema calcula a média ponderada das questões respondidas *dentro* de uma dimensão.
```python
# Para cada pergunta respondida:
pontos_obtidos = peso_pergunta * resposta_normalizada (0 a 100)

# Para a dimensão inteira:
score_dimensao = soma(pontos_obtidos) / soma(peso_das_perguntas_respondidas)
```
*Invariante:* Uma dimensão só recebe score se o usuário responder pelo menos 60% de suas questões.

### Passo 2: Score Geral (Global)
Agrega-se as dimensões aplicando o Peso da Dimensão.
```python
score_geral = soma(score_dimensao * peso_dimensao) / soma(peso_dimensao)
```
O resultado é um `ScoreNumerico` final em um range estrito de `0.0` a `100.0`.

### Passo 3: Score Específico PDCA (ABNT NBR 17301)
As 5 perguntas da Dimensão 7 são reagrupadas para gerar um radar de governança:
- **Plan:** Perguntas de Política (Q-ABNT-001) e Avaliação de Risco (Q-ABNT-002)
- **Do:** Perguntas de Controles Operacionais (Q-ABNT-003)
- **Check:** Monitoramento Contínuo (Q-ABNT-002 + Q-ABNT-004)
- **Act:** Melhoria Sistemática (Q-ABNT-005)

---

## 4. Classificação de Maturidade e Gaps

Com o `ScoreNumerico` calculado, o sistema define o `NivelMaturidade` que será estampado no relatório do usuário:
- **0 a 20:** Crítico
- **21 a 40:** Inicial
- **41 a 60:** Intermediário
- **61 a 80:** Avançado
- **81 a 100:** Exemplar

**Definição de Gap Crítico:**
Qualquer pergunta cuja relação `pontos_obtidos / peso_pergunta` seja inferior a `0.4` (ou seja, 40% do potencial da questão) é sinalizada como um *Gap*. Gaps nas dimensões Fiscal, Tecnológica ou ABNT são automaticamente classificados como de **Alta Criticidade**.
