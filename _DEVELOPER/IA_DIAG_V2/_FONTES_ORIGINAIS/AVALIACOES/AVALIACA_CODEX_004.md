# AVALIACA_CODEX_004 — Avaliação da Contra-Tréplica Claude (`AVALIACA_CODEX_003`)

> **Tipo:** avaliação final de resposta  
> **Avaliador:** Codex  
> **Data:** 2026-05-17  
> **Objeto:** `AVALIACA_CODEX_003.md`  
> **Veredito:** boa síntese de convergência, mas ainda precisa correção de cronograma, redução de escopo e separação entre decisão executiva e arquitetura técnica.

---

## 1. Resposta Direta

A `AVALIACA_CODEX_003.md` é a melhor peça conciliatória da série até agora. Ela reconhece erros próprios, consolida convergências e propõe transformar o debate em ADR, que é o movimento correto.

Mas há três problemas relevantes: o cronograma está defasado em relação à data atual, algumas exigências ainda tentam antecipar complexidade para a Fase 0, e a proposta de 8 fases continua grande demais para Allan conduzir sem uma priorização MVP da própria iniciativa de IA.

---

## 2. Pontos Fortes da Resposta

| Ponto | Avaliação |
|---|---|
| Reconhecimento de erro metodológico | Excelente. Claude admitiu que avaliou Fase 0 com régua de Fase 4. |
| Recalibração das notas | Boa. Corrigiu a autoavaliação 10/10 e trouxe mais honestidade. |
| Consolidação de convergências | Muito útil. A tabela de 11 convergências reduz ruído. |
| Proposta de ADR | Correta. O debate já gerou material suficiente para uma decisão formal. |
| Defesa de guardrails programáticos | Correta. Rubrica humana não substitui bloqueio automático. |
| RAG piloto antes de Lexiq completa | Correto. Evita full scan organizacional sem prova de recall. |
| Auditoria dos adapters existentes | Correto. Evita duplicar infraestrutura LLM já existente no QDI. |

---

## 3. Pontos Problemáticos

### 3.1 Cronograma impossível na data atual

O documento afirma:

```text
Pronto para 30/jun/2026 se iniciar até 21/abr/2026.
Atraso vermelho se iniciar depois de 30/abr.
```

Hoje é **17/mai/2026**. Portanto, as datas de corte já passaram:

- 21/abr/2026 passou há 26 dias.
- 30/abr/2026 passou há 17 dias.
- 30/jun/2026 está a 44 dias.

Com o próprio plano estimando aproximadamente **105h**, seria necessário executar cerca de:

```text
105h / 44 dias = 2,39h por dia corrido
```

Ou, considerando apenas dias úteis até 30/jun/2026, a carga diária ficaria ainda maior. Isso conflita com o ritmo saudável de Allan e com o fato de o QDI já ter outras frentes.

**Correção recomendada:** substituir o cronograma por um plano realista:

| Marco | Novo alvo sugerido |
|---|---|
| Fase A + B | até 31/mai/2026 |
| Fase C | até 07/jun/2026 |
| Fase D RAG piloto | até 21/jun/2026 |
| Decisão go/no-go para expansão | até 28/jun/2026 |
| Camadas E-H | pós-MVP ou Onda IA 1.1 |

---

### 3.2 A resposta quer encerrar o debate, mas ainda adiciona escopo

Claude propõe encerrar a rodada avaliativa, o que é sensato. Porém, ao mesmo tempo, adiciona:

- Fase A1;
- logs estruturados desde Fase A;
- `tenant_id` em todos os templates;
- schema pgvector com confiabilidade A/B/C/D;
- Checkpointer antes de 30/jun/2026;
- OTel + Jaeger;
- 50 golden questions;
- Lexiq completa.

Isso é uma tensão interna: o texto quer fechar decisão, mas segue ampliando o pacote.

**Correção recomendada:** separar em dois documentos:

1. `ADR-IA-001`: decisão estratégica enxuta.
2. `ROADMAP_IA_LOCAL_V1`: backlog faseado, com itens opcionais e gates.

---

### 3.3 Multi-tenant na Fase 0 precisa ser conceitual, não operacional

Claude defende `tenant_id` desde a Fase 0 em todos os templates. A ideia é boa, mas há risco de burocratizar o material de estudo.

Melhor abordagem:

| Artefato | `tenant_id` agora? | Motivo |
|---|---:|---|
| Catálogo de fontes globais | Sim, usar `tenant_id: shared` | Fonte normativa é global. |
| Casos supervisionados | Opcional | São treinamento, não dado de cliente. |
| Logs de benchmark | Sim | Ajuda rastreabilidade. |
| RAG pgvector | Sim | Já prepara multi-tenant. |
| Modelfile | Não | Persona não é tenant-specific. |

**Decisão recomendada:** usar `tenant_id` apenas onde houver persistência, logs ou dado recuperável.

---

### 3.4 OTel desde Fase A pode virar distração

Claude argumenta que logs estruturados desde o `ask_qdi.sh` custam 15 minutos. Na prática, o custo maior não é escrever JSON; é manter o padrão, interpretar os logs e não confundir isso com observabilidade real.

Concordo com log mínimo, mas não com chamar isso de OpenTelemetry.

**Correção recomendada para Fase A:**

```text
log local JSONL simples: sim
OpenTelemetry/Jaeger: não ainda
```

Campos mínimos:

```json
{
  "timestamp": "...",
  "modelo": "...",
  "latencia_ms": 0,
  "status": "ok|erro|timeout",
  "pergunta_hash": "sha256:..."
}
```

---

### 3.5 Checkpointer antes de 30/jun/2026 é discutível

Claude trata o Checkpointer como necessário antes da Onda 1.0 porque o wizard é multi-turno. Conceitualmente está certo para produto final, mas a pergunta desta trilha era memória/contexto local para estudo e desenvolvimento com Ollama.

Para o MVP/QDI, a prioridade deve depender do wizard real:

- Se o wizard atual já persiste diagnóstico/respostas no banco, LangGraph Checkpointer pode esperar.
- Se o wizard depende de estado volátil em memória, persistência deve subir de prioridade.

**Decisão recomendada:** antes de aceitar Checkpointer na Onda 1.0, auditar o fluxo atual do wizard e persistência já existente.

---

### 3.6 A pendência de acentuação é válida, mas não bloqueadora

Claude insistiu no problema de arquivos sem acentos. A crítica é procedente para material final em PT-BR. Porém, isso não deve bloquear Fase A.

**Decisão recomendada:**

- Documentação final: com acentuação.
- Scripts e paths: ASCII quando útil.
- Modelfile: com PT-BR acentuado, porque influencia estilo de resposta.

---

## 4. Decisões Que Eu Aceitaria da `AVALIACA_CODEX_003`

| Decisão | Status |
|---|---|
| Encerrar rodada avaliativa textual | Aceitar |
| Promover conteúdo para ADR | Aceitar |
| Rodar Fase A antes de qualquer implementação pesada | Aceitar |
| Fazer auditoria dos adapters existentes | Aceitar |
| Usar pgvector como alvo de RAG | Aceitar |
| Usar corpus piloto antes de Lexiq completa | Aceitar |
| Rubrica manual + golden questions | Aceitar |
| Catálogo A/B/C/D como metadado futuro | Aceitar |
| Threshold `0,65` provisório, calibrado depois | Aceitar com ressalva |

---

## 5. Decisões Que Eu Ajustaria

| Proposta da resposta | Ajuste recomendado |
|---|---|
| 8 fases A-H antes de 30/jun/2026 | Reduzir para Fases A-D antes de 30/jun; E-H ficam pós-gate. |
| `tenant_id` em todos os artefatos | Usar apenas em persistência, logs, RAG e dados recuperáveis. |
| OTel desde Fase A | Começar com JSONL local; OTel/Jaeger depois. |
| Checkpointer antes da Onda 1.0 | Auditar persistência atual do wizard antes de decidir. |
| Encerrar com ADR completo de 8 fases | Criar ADR enxuto + roadmap separado. |
| "Rodadas adicionais seriam diminishing returns" | Concordo, salvo após benchmark real. |

---

## 6. Proposta de Encaminhamento Final

Em vez de criar um ADR gigante, recomendo criar dois arquivos:

```text
ADR-IA-001-estrategia-hibrida-memoria-rag-local.md
ROADMAP_IA_LOCAL_QDI_V1.md
```

### ADR-IA-001 deve decidir somente:

1. Adotar abordagem híbrida Codex + Claude.
2. Usar gates técnicos curtos.
3. Priorizar estabilidade Ollama antes de arquitetura.
4. Usar pgvector como destino RAG.
5. Usar catálogo A/B/C/D.
6. Reconciliar com adapters existentes antes de criar novos.

### ROADMAP deve conter:

1. Fase A: estabilizar Ollama.
2. Fase B: benchmark mínimo.
3. Fase C: memória supervisionada.
4. Fase D: RAG piloto.
5. Fase E: integração Python/router.
6. Fase F: indexação de código.
7. Fase G: checkpointer/observabilidade.
8. Fase H: Lexiq completa.

Assim, a decisão arquitetural fica limpa e o plano operacional continua ajustável.

---

## 7. Veredito Final

A `AVALIACA_CODEX_003.md` é uma boa resposta e deve ser considerada o encerramento saudável da rodada de debate. Ela demonstra maturidade ao reconhecer erros e convergir para um plano híbrido.

Minha crítica principal é que o documento ainda tenta carregar escopo demais para uma janela que, em **17/mai/2026**, já não comporta as 105h previstas antes de 30/jun/2026 sem risco de sobrecarga e dispersão.

**Decisão recomendada:** aceitar a síntese, mas transformar em um ADR enxuto e um roadmap separado. Antes disso, executar somente a Fase A: estabilizar Ollama e gerar dados reais. A próxima avaliação útil deve nascer de benchmark, não de mais argumentação textual.

