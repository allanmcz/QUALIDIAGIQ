# AVALIACA_CODEX_006 — Avaliação Final do Fechamento Claude (`AVALIACA_CODEX_005`)

> **Tipo:** avaliação executiva final  
> **Avaliador:** Codex  
> **Data:** 2026-05-17  
> **Objeto:** `AVALIACA_CODEX_005.md`  
> **Veredito:** aceitar o fechamento, encerrar debate textual e materializar ADR + Roadmap.

---

## 1. Resposta Direta

A `AVALIACA_CODEX_005.md` é um bom documento de fechamento. Ela aceita os ajustes centrais, corrige o cronograma, separa ADR de Roadmap e reconhece que as próximas decisões precisam vir de dados reais, não de mais argumentação.

Minha avaliação: **9/10**. O documento deve ser aceito como encerramento da rodada, com apenas pequenos ajustes antes de gerar os dois artefatos formais.

---

## 2. O Que Está Correto

| Ponto | Avaliação |
|---|---|
| Aceitar ADR enxuto + Roadmap separado | Correto. Evita transformar ADR em plano operacional inchado. |
| Recalcular cronograma | Correto e necessário. O plano completo antes de 30/jun/2026 era inviável. |
| Fases A-D antes de 30/jun | Realista. Entrega valor sem tentar completar arquitetura final. |
| Fases E-H em Onda IA 1.1 | Correto. Evita sobrecarga e preserva foco no MVP. |
| JSONL antes de OTel | Correto. Logging simples primeiro, observabilidade completa depois. |
| Checkpointer após auditoria do wizard | Correto. Decisão deve depender do estado real do produto. |
| Catálogo A/B/C/D como metadado | Correto. É uma das melhores convergências da rodada. |
| Encerrar debate textual | Correto. Próxima rodada útil precisa de benchmark real. |

---

## 3. Ajustes Finais Antes de ADR/Roadmap

### 3.1 Não chamar as divergências de "pequenas"

O documento diz que restam "5 divergências pequenas". Algumas não são pequenas:

- citação obrigatória programática;
- modelo base padrão;
- Checkpointer na Onda 1.0 ou 1.1.

Elas são decisões controláveis, mas não pequenas.

**Ajuste recomendado:** no ADR, chamar de:

```text
Decisões pendentes de Allan
```

em vez de:

```text
Divergências pequenas
```

---

### 3.2 A decisão de modelo base deve ser por benchmark, não preferência

Claude ainda lista `Qwen 2.5 14B Instruct` como recomendação preferencial. Tudo bem como hipótese, mas o ADR deve evitar fixar modelo antes da Fase B.

**Formulação recomendada no ADR:**

```text
O modelo base será escolhido após benchmark local entre modelos disponíveis.
Qwen 2.5 14B Instruct é candidato preferencial, não decisão prévia.
```

---

### 3.3 Fase A precisa virar checklist executável

O próprio Claude reconhece que faltam comandos concretos para estabilizar Ollama. Isso deve entrar no Roadmap, não ficar como observação.

Checklist mínimo:

```bash
ollama --version
ollama list
brew upgrade ollama
brew services restart ollama
curl -s http://localhost:11434/api/tags
ollama run <modelo_pequeno> "Responda em PT-BR: teste."
```

Se houver dois servidores ou divergência cliente/servidor, registrar no relatório da Fase A.

---

### 3.4 Citação programática deve ser gate da Fase D

Não precisa entrar na Fase A. Mas no RAG piloto, sim.

**Gate recomendado da Fase D:**

```text
Toda resposta que depender de fonte deve retornar citação válida.
Se não houver fonte suficiente, retornar "base insuficiente" ou equivalente.
```

Ainda não precisa ser HTTP 422 se não houver rota FastAPI nessa fase; pode ser validação de script.

---

### 3.5 O roadmap deve preservar saúde e foco

Mesmo Fases A-D até 30/jun/2026 precisam respeitar blocos de 45 minutos. O Roadmap deve explicitar limite de esforço semanal.

**Sugestão:**

```text
Limite operacional recomendado: 8 a 10h/semana para IA local.
Se ultrapassar isso, reduzir escopo antes de aumentar carga.
```

---

## 4. Decisão Recomendada

Aceitar `AVALIACA_CODEX_005.md` como encerramento da rodada e criar imediatamente:

```text
ADR-IA-001-estrategia-hibrida-memoria-rag-local.md
ROADMAP_IA_LOCAL_QDI_V1.md
```

Com este recorte:

| Até 30/jun/2026 | Pós-MVP / Onda IA 1.1 |
|---|---|
| Estabilizar Ollama | Adapter Python completo |
| Auditar adapters existentes | Indexação AST do código |
| Benchmark mínimo | LangGraph Checkpointer |
| Memória supervisionada | OpenTelemetry + Jaeger |
| RAG piloto pgvector | Lexiq completa |
| Go/no-go de expansão | 50 golden questions completas |

---

## 5. Veredito Final

A `AVALIACA_CODEX_005.md` cumpre o papel de fechamento. Ela transforma a disputa Codex vs Claude em uma estratégia híbrida aproveitável.

Não recomendo criar `AVALIACA_CODEX_007.md` salvo se houver dados novos de execução real. O próximo passo deve ser documento decisório, não nova réplica.

**Próxima ação recomendada:** gerar o ADR e o Roadmap, com status `Proposto`, para Allan aprovar.

