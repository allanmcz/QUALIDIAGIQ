# Cenário **D** — Demonstração + consultoria supervisionada (MacBook, sem público)

> **Data:** 2026-05-03  
> **Uso:** quando **não** há go-live em cloud nem site público — apenas **demo** e **consultoria supervisionada** contigo no **MacBook** (Docker local / OrbStack, `make dev`).

---

## 1. O que muda face ao pacote original (A/B)

| Tema | Plano A/B (go-live / institucional) | Cenário **D** (demo local) |
|------|--------------------------------------|----------------------------|
| **D4** URL canónica, DNS, CORS produção | Obrigatório em **A** para prod | **Fora de escopo** — basta `localhost` (60000/60001) documentado |
| **P6** RLS no Supabase **cloud** | Opcional com dispensa em A | **Dispensado por defeito** — já tens evidência **Docker/CI** (`make mvp-gate`) |
| **P5b** “espelho” igual a produção | Paridade imagem/env prod | **Reduzido** a **paridade local**: mesmo `docker-compose`, mesma imagem API, mesmas env de PDF que usas nas demos |
| **Tag + CHANGELOG** release público | A6 em critérios A | **Opcional** — podes usar só **commit SHA** + nota em `_DEVELOPER/MVP_05052026/` ou tag interna `demo-2026-05-05` |
| **Jurídico** parecer formal termos/privacidade para **comercialização** | Bloqueia **B** | **Não bloqueia D** para demo interna, **desde que** (ver §2) |
| **3 contadores externos** (checklist sec. 5) | MUST comercial | **Fora do corte D** — és tu o supervisor |
| **OTEL / observabilidade prod** | Stretch | **Opcional** |
| **Billing D5** | Decisão produto | **Irrelevante** para D |

**Analogia (Delphi/Winthor):** é um **ambiente de homologação na máquina do consultor** com base **restaurada** — não exiges **DNS público** nem **cópia idêntica ao data center** para validar fluxo com o cliente ao telefone.

---

## 2. LGPD e dados reais (não “acelerar” à custa da lei)

Cenário **D** **não** elimina LC **13.709/2018** se entrares **dados pessoais reais** (e-mail, telefone, CNPJ identificável) no wizard ou no PDF.

| Modo | Recomendação |
|------|----------------|
| **Demo com dados fictícios** | Preferível para acelerar — fixtures / CNPJs de teste já usados em QA. |
| **Consultoria supervisionada com dados reais** | Base legal + minimização + registo de **finalidade** (ex.: sessão de análise sob teu mando); idealmente **termo curto** com o cliente ou uso apenas de dados já licenciados ao teu escritório. **Não** substitui parecer jurídico para **produto SaaS público** — mas o risco é outro. |

### 2.1 Decisão registada (handoff **MVP_05052026** — 2026-05-05)

- **Congelamento (F0.1):** sem novas features **SHOULD** até novo corte; apenas **P0/P1** no repositório.  
- **Dados demo (F0.2):** **fictícios preferidos** nas demos gravadas; dados reais só com regra da tabela acima.

---

## 3. Lista mínima para declarar **“MVP-D pronto”** (acelerado)

1. `make dev` + `make migrate` no MacBook — fluxo wizard → diagnóstico → dashboard → PDF **uma vez** gravado (vídeo ou PDF sem PII).  
2. `make test` + `make mvp-gate` verdes na branch que usas na demo.  
3. `PDF_HOMOLOGACAO_CHECKLIST_B1.md` — apenas itens **objetivos** que impactam leitura do relatório na demo (sem “sign-off de terceiros”).  
4. Roteiro de 1 página: **5 minutos** de demo + **10 minutos** de consultoria (perguntas que queres que o cliente faça).  

---

## 4. O que **não** cortar (qualidade mínima Tributiq)

- **Segredos** só em `.env` / settings — nunca no código.  
- **RLS** no Postgres local com as migrações do repo (já coberto por testes — não desativar para “ir mais rápido”).  
- **Idempotência** e JWT nos fluxos que mostras se fores repetir POST na demo.

---

## 5. Onde está espelhado nos outros ficheiros

- **Plano HANDOFF de execução:** [`HANDOFF_PLANO_EXECUCAO_MVP_05052026.md`](./HANDOFF_PLANO_EXECUCAO_MVP_05052026.md) (fases F0–F4, Z1–Z11).  
- Critérios formais alinhados a **D:** [`02_CRITERIOS_ACEITE_EVIDENCIAS.md`](./02_CRITERIOS_ACEITE_EVIDENCIAS.md) — secção **2**.  
- Gaps atualizados: [`01_AVALIACAO_GAP_MVP_100.md`](./01_AVALIACAO_GAP_MVP_100.md) — secção **1** (definição **D**).  
- Prompt agente: [`05_PROMPT_AGENTE_FECHO_MVP.md`](./05_PROMPT_AGENTE_FECHO_MVP.md).

---

*Índice da pasta:* [`README.md`](./README.md)
