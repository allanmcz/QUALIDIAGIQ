# Avaliacao Executiva do Plano de Implantacao QDI

## Resposta direta

O projeto ja possui um motor de plano de implantacao funcional e coerente com o MVP: ele materializa checklist, matriz de impacto e cronograma a partir do diagnostico finalizado. O ponto mais forte e a combinacao de score por dimensao com a frente automatica das tres maiores lacunas; o ponto a melhorar e que as acoes ainda sao majoritariamente por dimensao e porte, nao por pergunta respondida, segmento economico, regime tributario e severidade individual do gap.

## O que existe hoje

| Bloco | Situacao atual | Observacao |
|---|---|---|
| Questionario | 37 perguntas versionadas em JSON | 7 dimensoes: fiscal, estrategica, contabil, financeira, operacional, tecnologica e compliance ABNT. |
| Score | Media ponderada por pergunta e peso macro por dimensao | Fiscal pesa 1,5; tecnologica 1,3; ABNT 1,2; demais 1,0. |
| Plano dinamico | 3 piores dimensoes geram 3 acoes cada | Gera ate 9 acoes prioritarias por score. |
| Plano fixo | Governanca, contratos, ABNT e, para medio/grande, TI/ERP e cadastros | Gera 14 acoes para empresas menores e 18 para medio/grande, antes do bloco dinamico. |
| Matriz departamental | 6 departamentos fixos | Fiscal, Comercial, TI, Juridico, Financeiro/Controladoria e RH/Folha. |
| Cronograma | 5 fases temporais | 0-12m, 12-24m, 24-36m, 36-60m, 60-96m. |
| Quadro de implantacao | Persistencia de anotacoes por acao | Suporta prazo meta, comentarios e descricao personalizada. |

## Leitura de aderencia ao PRD e MoSCoW

| Feature | Evidencia atual | Avaliacao |
|---|---|---|
| M01 — Wizard adaptativo | Existe filtro por `condicao` de setor, porte e regime | Bom inicio; precisa melhorar equilibrio por segmento. |
| M02 — Score 0-100 com 7 dimensoes | Implementado no motor de score | Aderente. |
| M03 — Pesos transparentes | Pesos por pergunta no catalogo e pesos macro versionaveis | Aderente; falta manifesto mais legivel para usuario final. |
| M06 — Cronograma de implementacao | Implementado em 5 fases | Aderente; falta relacionar fase com acao/pergunta. |
| M07 — Recomendacoes priorizadas | Implementado por pior dimensao | Parcial; falta granularidade por pergunta. |
| M08 — Ancoragem legal por bullet | Presente nas perguntas e acoes | Bom; precisa validar citacoes juridicamente e versionar por vigencia. |
| M11/M12 — ABNT 17301 | Perguntas ABNT + checklist de 10 controles | Aderente; falta score PDCA detalhado por eixo. |

## Principais achados

1. **O plano e operacionalmente util**, porque ja entrega responsavel, prazo, criticidade, base legal e prioridade.
2. **A personalizacao ainda e limitada**, porque a frente automatica olha as tres piores dimensoes, mas nao sabe qual pergunta especifica derrubou a dimensao.
3. **O segmento entra no questionario, mas pouco no plano**, porque o checklist final nao diferencia varejo, industria, servicos e agro, exceto pelo efeito indireto do score fiscal.
4. **A matriz departamental e fixa**, boa para MVP, mas deve passar a refletir setor, porte, regime e respostas criticas.
5. **O quadro de implantacao esta bem desenhado**, mas precisa de status, dono real, evidencia anexada e relacao com subtarefas para virar ferramenta de acompanhamento serio.

## Analogia pratica

Pense no plano atual como uma rotina Winthor que ja gera uma agenda de tarefas por modulo, mas ainda nao abre o detalhe por transacao que causou o erro. Ele sabe que o modulo Fiscal esta vermelho; o proximo salto e apontar se o vermelho veio de ICMS-ST, NFS-e, cClassTrib, contratos, creditos acumulados ou ausencia de PDCA ABNT.

## Recomendacao executiva

Manter o motor atual como **baseline MVP v1** e evoluir para um **Plano de Implantacao v2 orientado a evidencias**, com quatro chaves de decisao:

| Chave | Como usar |
|---|---|
| Dimensao | Define a frente macro e o peso executivo. |
| Pergunta | Define a acao especifica e a evidencia esperada. |
| Segmento | Ajusta linguagem, risco e artefato de entrega. |
| Regime/porte | Ajusta complexidade, prioridade e necessidade de governanca formal. |

