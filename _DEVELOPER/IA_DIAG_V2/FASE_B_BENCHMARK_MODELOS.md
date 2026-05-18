# Fase B — Benchmark de Modelos Locais

## Objetivo

Escolher o modelo base por evidencia local, considerando qualidade em PT-BR, aderencia ao QDI, citacao de fontes, raciocinio arquitetural e latencia.

## Modelos candidatos

A lista final depende do `ollama list` da Fase A.

Candidatos preferenciais:

| Modelo | Papel |
|---|---|
| Qwen 2.5 14B Instruct | candidato de qualidade principal |
| Llama 3.1/3.2 8B Instruct | candidato leve e rapido |
| Phi/Mistral disponivel | candidato alternativo |

## Perguntas de benchmark

### P1 — Persona e escopo

```text
Explique em 6 frases o que e o QualiDiagIQ, qual o escopo do MVP e o que fica fora do MVP.
```

### P2 — Clean Architecture

```text
No QDI, onde devo implementar uma regra pura de calculo de score tributario e onde devo implementar o caso de uso que salva o resultado?
```

### P3 — Fonte tributaria

```text
Responda com cautela: uma resposta sobre CBS/IBS pode ser aceita sem citacao de fonte normativa? Explique a politica correta.
```

### P4 — RAG e base insuficiente

```text
Se a base local nao tiver fonte primaria suficiente sobre uma regra tributaria, como o agente deve responder?
```

### P5 — Codigo existente

```text
O QDI ja possui gateway LLM e adapters. Voce deve criar um novo adapter do zero ou auditar e evoluir o existente? Justifique.
```

## Rubrica

Nota de 0 a 3 por criterio:

| Criterio | 0 | 1 | 2 | 3 |
|---|---|---|---|---|
| PT-BR | ruim | compreensivel | bom | excelente |
| QDI | generico | cita QDI | entende escopo | entende escopo e limites |
| Arquitetura | errado | parcial | correto | correto e acionavel |
| Fonte | ignora | cita genericamente | exige fonte | exige fonte/base insuficiente |
| Acionabilidade | vago | pouca acao | aplicavel | pronto para executar |
| Latencia | travou | lenta | aceitavel | fluida |

## Comando sugerido

```bash
ollama run <modelo> "<pergunta>"
```

Registre cada resposta usando:

```text
templates/BENCHMARK_RESPOSTA_TEMPLATE.md
```

## Saida esperada

Criar:

```text
reports/FASE_B_BENCHMARK_MODELOS.md
```

Com:

- modelos testados;
- tempo aproximado por resposta;
- notas por criterio;
- melhor modelo geral;
- melhor modelo leve;
- decisao recomendada para Fase C/D.

## Criterio de escolha

Nao basta o modelo escrever bonito. Para o QDI, o vencedor precisa:

- respeitar escopo;
- nao inventar fonte;
- saber recusar quando faltar base;
- orientar codigo dentro de `src/`;
- nao propor arquitetura paralela sem necessidade.

