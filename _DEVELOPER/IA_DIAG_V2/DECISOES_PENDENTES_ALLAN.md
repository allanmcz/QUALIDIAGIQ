# Decisoes de Allan — IA_DIAG_V2

> Painel de controle. Atualizado em **2026-05-17** após catalogação de `dominio_fiscal/`.

## Resumo

| ID | Tema | Status |
|----|------|--------|
| DP-001 | Modelos do benchmark | **Decidido** |
| DP-002 | Corpus piloto RAG | **Decidido** |
| DP-003 | Local fisico das fontes | **Decidido** |
| DP-004 | Integracao ao codigo | **Decidido** |
| DP-005 | Limite operacional semanal | **Decidido** |
| DP-006 | Gate de citacao | **Decidido** |

---

## DP-001 — Modelos que entram no benchmark

**Status:** Decidido (2026-05-17)

Modelos candidatos:

- [ ] Qwen 2.5 14B Instruct (pull dedicado)
- [ ] Llama 3.1/3.2 8B Instruct (pull dedicado)
- [ ] Phi ou Mistral local disponivel
- [x] Apenas modelos ja instalados no Ollama

Decisao:

```text
Benchmark Fase B apenas com modelos ja presentes em `ollama list` (sem pull obrigatorio).
Candidatos observados no ambiente: qwen2.5-coder:14b, llama3.2:latest, qwen2.5:32b-instruct,
qdi-assistant:latest, mxbai-embed-large (embedding). Matriz 3 modelos x 5 perguntas.
```

---

## DP-002 — Corpus piloto do RAG

**Status:** Decidido (2026-05-17)

Opcoes:

- [ ] Legislacao oficial apenas
- [x] Legislacao oficial + documentos QDI
- [ ] Legislacao oficial + docs QDI + aulas/anotacoes com confiabilidade C

Decisao:

```text
Corpus piloto = classe A em dominio_fiscal/ (EC 132, LC 214, NT 2025.002 v1.35, cClassTrib,
cCredPres, manuais RTC selecionados) + classe B em docs/refs/ (PRD, MoSCoW, metodologia,
questionario). Pastas 06/07 e guias de terceiros (Taxcel) ficam fora do indice normativo inicial.
Catalogo: dominio_fiscal/catalogo_fontes.yml
```

---

## DP-003 — Local fisico das fontes

**Status:** Decidido (2026-05-17)

Opcoes:

- [x] `dominio_fiscal/`
- [ ] `docs/legal/`
- [ ] `_DEVELOPER/IA_DIAG_V2/fontes/`
- [ ] outro local definido por Allan

Decisao:

```text
Fontes brutas tributarias em dominio_fiscal/ (58 ficheiros, ~43 MB, 8 subpastas numeradas).
Documentos QDI ja incorporados permanecem em docs/refs/ e docs/legal/.
Indice humano: dominio_fiscal/INDEX.md
```

---

## DP-004 — Momento de integrar ao codigo

**Status:** Decidido (2026-05-17)

Opcoes:

- [x] Scripts locais primeiro, sem alterar `src/`
- [ ] Branch de adapter apos Fase B
- [ ] Integracao direta ao gateway existente apos Fase A

Decisao:

```text
Fases A-D sem alterar src/ nem frontend/. Integracao ao gateway_router e adapters existentes
(llm_ollama, llm_langgraph_ollama) somente apos Fase B (benchmark) + RAG piloto validado (Fase D)
e go/no-go explicito (Fase E — Onda IA 1.1).
```

---

## DP-005 — Limite operacional semanal

**Status:** Decidido (2026-05-17)

Opcoes:

- [ ] 8h/semana
- [ ] 10h/semana
- [x] outro limite: **14h/semana**

Decisao:

```text
14 horas por semana para IA local (acima da recomendacao V2 de 8-10h, decisao consciente do Allan).
Manter blocos de 45 minutos com pausas (saúde). Reavaliar se competir com fechamento do MVP.
```

---

## DP-006 — Gate de citacao

**Status:** Decidido (2026-05-17)

Opcao:

```text
Toda resposta tributaria baseada em RAG deve retornar fonte identificavel (id do catalogo_fontes.yml).
Se nao houver fonte primaria suficiente (classe A ou B aplicavel), responder "base insuficiente".
```

Marcar:

- [x] Aprovado
- [ ] Ajustar texto do gate

---

## Proximo passo operacional

1. Executar **Fase A** (`FASE_A_CHECKLIST_OLLAMA.md`) → `reports/FASE_A_RELATORIO.md`
2. Executar **Fase B** com modelos do `ollama list` (DP-001)
3. **Fase D:** extrair PDFs/XLSX do piloto e validar retriever contra `catalogo_fontes.yml`
