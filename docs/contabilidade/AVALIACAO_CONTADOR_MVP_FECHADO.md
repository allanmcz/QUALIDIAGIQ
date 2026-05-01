# Avaliação contábil, fiscal e de compliance — MVP QualiDiagIQ

**Público:** contador responsável, fiscalista, controller ou assessor que avalia se o produto pode ser recomendado ou contratado com **defensividade profissional**.

**Objetivo:** lista objetiva do que conferir, em linguagem de negócio, sem exigir leitura de código.

**Base normativa de referência do produto:** EC 132/2023; LC 214/2025; ABNT NBR 17301:2026 (compliance tributário); LGPD Lei 13.709/2018 (tratamento de dados no fluxo do diagnóstico).

---

## 1. O que o QualiDiagIQ é — e o que não é

| Afirmação | Você deve validar |
|-----------|-------------------|
| **É** uma ferramenta de **diagnóstico de maturidade** frente à Reforma do Consumo e boas práticas de compliance tributário (incluindo eixo ABNT). | Se o escopo atende à expectativa do cliente interno/externo. |
| **É** um insumo para **priorização** de projetos (gaps, cronograma sugerido, matriz por área). | Se os outputs são úteis para governança e não substituem trabalho técnico detalhado. |
| **Não é** apuração de CBS/IBS/IS nem substituição de ERP (**apuração contínua é outro módulo do ecossistema — QAI**). | Registrar por escrito que **não há promessa de apuração**. |
| **Não é** parecer fiscal individualizado com responsabilidade técnica **CRC** sobre um caso concreto sem revisão humana. | Delimitar na proposta comercial que o **usuário** responde pelo conteúdo das respostas ao questionário (**boa fé informacional**). |
| **Não é** defesa em auto de infração nem auditoria independente. | Evitar linguagem de “certificação” ou “aprovação da Receita”. |

---

## 2. Transparência do score (M02 / M03)

**Risco reputacional:** score 0–100 sem metodologia auditável é fragilidade.

**Checklist:**

- [ ] Conferir a página **`/metodologia`** no front (manifesto de pesos e fórmula do score geral).
- [ ] Conferir o endpoint público **`GET /diagnosticos/manifesto-pesos`** (JSON com pesos por pergunta e macros por dimensão).
- [ ] Conferir **`GET /diagnosticos/metodologia`** (coerência com o motor declarado).
- [ ] Validar se a **ponderação** (dimensão Fiscal mais pesada que outras, ABNT como eixo explícito) está **alinhada ao discurso comercial** do Tributiq.

**Aceite sugerido:** “Metodologia de score e pesos está documentada de forma suficiente para auditoria interna do cliente.”

---

## 3. Ancoragem normativa nos textos (M08)

**Risco:** bullets genéricos sem dispositivo geram **marketing fiscal** indefensável.

**Checklist:**

- [ ] Amostrar recomendações/checklist no relatório ou UI e verificar se há **referência explícita** (ex.: LC 214/2025 art. X, NT Y, ABNT cap. Z).
- [ ] Onde houver texto gerado por **IA**, confirmar no produto se existe **guardrail** (rejeição sem fonte) — ver política de produto vigente.

**Aceite sugerido:** “Amostragem de âncoras normativas considerada adequada / inadequada (descrever gaps).”

---

## 4. Relatório PDF (M04 / P5)

**Checklist (operacional detalhado pode existir em runbook interno de homologação PDF / P5):**

- [ ] Capa e identificação da empresa/diagnóstico.
- [ ] Síntese executiva legível para diretoria não técnica.
- [ ] Detalhamento por dimensão coerente com o score exibido na tela.
- [ ] Cronograma em horizontes **alinhado ao discurso da LC 214/2025** (referência citada no template).
- [ ] Matriz de impacto por área com **criticidade** e base legal.
- [ ] Rodapé / disclaimer com **EC 132/2023**, **LC 214/2025**, **ABNT NBR 17301:2026** e limitação de responsabilidade.

**Produção:** confirmar que em **produção** o PDF é gerado com **WeasyPrint real** (sem stub mascarado como entrega).

---

## 5. Evidências, integridade e LGPD

**Auditoria interna (similar a trilha de log em ERP):**

- [ ] **Aceite de privacidade:** no fluxo de criação do diagnóstico, o sistema exige aceite e persiste **`aceite_termos_privacidade_em`** (instante servidor, UTC). Isso sustenta demonstração de **ciência** do titular (LGPD).
- [ ] **Imutabilidade pós-finalização (WORM):** após diagnóstico finalizado, campos de evidência (score, hash, etc.) não devem ser alterados arbitrariamente — alinha defesa com **previsibilidade** e **auditabilidade** (LC 214/2025 como horizonte sistêmico; ABNT 17301 como gestão de compliance).
- [ ] **Hash de evidência:** confirmar que o relatório ou API expõem **hash** ou snapshot coerente com o commitido ao cliente.

**LGPD (processo, não substitui advogado):**

- [ ] Ler **`/privacidade`** e **`/termos`** (versão MVP) e decidir se precisam de **substituição** por texto chancelado pelo escritório jurídico.
- [ ] Telefone do respondente: se coletado, está descrito como **opcional** e com **finalidade** e **retenção** alinhadas ao ciclo de vida do diagnóstico.

---

## 6. Confidencialidade e multi-tenant (M10)

**Risco:** vazamento de diagnóstico entre empresas.

**Checklist:**

- [ ] Confirmar com TI/produto que **RLS (Row Level Security)** está ativa no Postgres de **produção** e testada com **dois tenants**.
- [ ] Confirmar que **tenant_id** vem de **JWT** autenticado, não de header forjável.

**Aceite sugerido:** “Isolamento por tenant verificado em ambiente de homologação/produção (evidência anexada).”

---

## 7. Limitações que devem constar na proposta ao cliente

Sugerimos validar se o contrato ou termos incluem expressamente:

1. Dependência da **veracidade** das respostas do questionário.
2. Caráter **orientativo** do score e do PDF, sem garantia de resultado fiscal perante terceiros.
3. **Roadmap normativo:** LC 225 e alterações posteriores podem exigir atualização do produto (versionamento normativo é princípio do projeto).

---

## 8. Ferramentas que a engenharia pode mostrar (opcional)

Não são substituto do teu julgamento profissional, mas **reduzem custo de due diligence**:

| Artefacto | O que prova |
|-----------|-------------|
| `make test` / CI verde | Regressão automatizada do motor e da API. |
| `make mvp-gate` | Smoke crítico + schema **0012** + teste RLS dois tenants (ambiente com Postgres). |
| `make verify-schema-mvp` (script `scripts/verify_mvp_schema.py`) | Colunas LGPD/M12 e políticas RLS presentes no banco alvo. |

---

## 9. Sign-off (modelo)

| Campo | Preenchimento |
|-------|----------------|
| **Empresa avaliadora** | |
| **Profissional** | Nome completo e CRC (se aplicável) |
| **Data** | |
| **Escopo avaliado** | MVP QualiDiagIQ — diagnóstico web + PDF + multi-tenant |
| **Conclusão** | Aprovado para uso interno / piloto / homologação condicionada / não aprovado |
| **Condições ou ressalvas** | (texto livre — ex.: “pendente parecer jurídico”, “PDF ainda não homologado em produção”) |
| **Assinatura** | |

---

## 10. Referências rápidas no produto

- Front: **`/avaliacao-contador`**, **`/metodologia`**, **`/termos`**, **`/privacidade`**, **`/abnt-framework`**
- API (base configurável): **`/diagnosticos/manifesto-pesos`**, **`/diagnosticos/metodologia`**, **`/health`**

---

*Documento operacional do projeto QDI. Ajustar datas e caminhos se o ambiente do cliente divergir do Compose padrão.*
