# 09 — Benchmark e Avaliação (Golden Questions)

> **Objetivo:** definir a suite de avaliação para medir qualidade do Ollama vs Claude no domínio QDI.

---

## 1. Estrutura das Golden Questions

Total: **50 perguntas** distribuídas em 4 categorias:

| Categoria | Quantidade | Peso |
|-----------|-----------|------|
| Conceitos tributários básicos | 15 | 30% |
| Classificação cClassTrib específica | 10 | 25% |
| Arquitetura QDI (usa Camada 3) | 10 | 20% |
| Fluxos de wizard | 10 | 15% |
| Casos-limite (devem responder INDEFINIDO) | 5 | 10% |

---

## 2. Exemplos por Categoria

### Categoria A — Conceitos Tributários

```yaml
- id: A-01
  pergunta: "Qual a diferença entre CBS e IBS na LC 214/2025?"
  resposta_esperada_contem:
    - "CBS"
    - "União"
    - "IBS"
    - "Estados e Municípios"
  evidencia_obrigatoria:
    documento: "LC_214_2025"
    artigo_min: "Art. 1"

- id: A-02
  pergunta: "Em que ano a CBS começa a ser cobrada com alíquota plena?"
  resposta_esperada_contem: ["2027"]
  evidencia_obrigatoria:
    documento: "LC_214_2025"
```

### Categoria B — cClassTrib

```yaml
- id: B-01
  pergunta: "Qual cClassTrib para venda de produto sujeito a regime monofásico?"
  resposta_esperada_contem:
    - "monofásico"
    - "código"
  evidencia_obrigatoria:
    tipo: "tabela_cclasstrib"

- id: B-02
  pergunta: "cClassTrib 040101 corresponde a qual operação?"
  resposta_esperada_contem: ["alíquota padrão", "saída"]
```

### Categoria C — Arquitetura QDI

```yaml
- id: C-01
  pergunta: "Qual entity representa o diagnóstico finalizado no QDI?"
  resposta_esperada_contem: ["Diagnostico", "src/domain/entities"]
  evidencia_obrigatoria:
    camada: "DOMAIN"
    tipo_artefato: "ENTITY"

- id: C-02
  pergunta: "Em qual ADR está documentada a estratégia multi-tenant?"
  resposta_esperada_contem: ["ADR"]
  evidencia_obrigatoria:
    tipo_artefato: "ADR"
```

### Categoria D — Fluxos de Wizard

```yaml
- id: D-01
  pergunta: "Quais são os 7 eixos da ABNT NBR 17301?"
  resposta_esperada_contem:
    - "PDCA"
    - "compliance"
  qty_eixos_min: 5  # deve listar ao menos 5

- id: D-02
  pergunta: "Como o wizard QDI captura o porte da empresa?"
  resposta_esperada_contem: ["CNPJ", "porte", "Simples"]
```

### Categoria E — Casos-Limite (INDEFINIDO esperado)

```yaml
- id: E-01
  pergunta: "Qual a alíquota do ICMS para venda de tijolos em Goiás em 2025?"
  resposta_esperada_contem: ["INDEFINIDO", "fora do escopo"]
  observacao: "Pré-CBS — escopo do RestituIQ, não do QDI"

- id: E-02
  pergunta: "Como recuperar créditos de PIS/COFINS de 2024?"
  resposta_esperada_contem: ["INDEFINIDO", "outro produto"]
```

---

## 3. Métricas Calculadas

```python
@dataclass
class MetricasBenchmark:
    """Métricas agregadas de uma rodada de benchmark."""

    total_perguntas: int
    acertos: int  # contém todas as palavras esperadas
    parciais: int  # contém ≥ 50% das palavras
    falhas: int

    citacao_valida: int  # tem evidência apontada corretamente
    citacao_invalida: int  # cita doc inexistente ou errado

    latencia_p50_ms: int
    latencia_p95_ms: int
    latencia_p99_ms: int

    custo_total_usd: float

    @property
    def acuracia(self) -> float:
        return self.acertos / self.total_perguntas

    @property
    def taxa_citacao_valida(self) -> float:
        return self.citacao_valida / (self.citacao_valida + self.citacao_invalida)
```

---

## 4. Alvos Mínimos para Liberar Produção (Onda 1.0)

| Métrica | Alvo Ollama (dev) | Alvo Claude (prod) |
|---------|-------------------|---------------------|
| Acurácia categoria A | ≥ 90% | ≥ 98% |
| Acurácia categoria B | ≥ 85% | ≥ 95% |
| Acurácia categoria C | ≥ 90% | ≥ 95% |
| Acurácia categoria D | ≥ 85% | ≥ 95% |
| Acurácia categoria E (rejeição) | ≥ 95% | ≥ 99% |
| Taxa de citação válida | 100% | 100% |
| Latência p95 | < 30s | < 8s |

---

## 5. Script de Execução

```python
# _DEVELOPER/IA_DIAG_AVANCADO/SCRIPTS/golden_questions.py
"""
Executa as 50 golden questions contra Ollama (e opcionalmente Claude).

Gera relatório em REPORTS/benchmark_YYYYMMDD.json e .md
"""
import asyncio
import json
import time
from pathlib import Path
import yaml

QUESTOES_PATH = Path("golden_questions.yaml")
REPORTS_DIR = Path("REPORTS")


async def executar_benchmark():
    questoes = yaml.safe_load(QUESTOES_PATH.read_text())
    resultados = []

    for q in questoes:
        inicio = time.perf_counter()
        resposta = await llm_router.gerar_resposta(q["pergunta"])
        latencia_ms = int((time.perf_counter() - inicio) * 1000)

        acertou = all(p.lower() in resposta.conteudo.lower()
                      for p in q["resposta_esperada_contem"])

        resultados.append({
            "id": q["id"],
            "categoria": q["id"][0],
            "acertou": acertou,
            "latencia_ms": latencia_ms,
            "evidencias_citadas": len(resposta.evidencias),
        })

    # Agregar e salvar
    relatorio = agregar_metricas(resultados)
    salvar_relatorio(relatorio)
    return relatorio
```
