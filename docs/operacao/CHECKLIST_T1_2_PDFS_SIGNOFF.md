# Como fechar T1.2 — Cinco PDFs reais e sign-off contábil

**Objetivo:** homologar **cinco** relatórios WeasyPrint **reais** (um por macro-setor de calibração), com critérios M04/B.2/B.3 alinhados ao MVP, e formalizar **sign-off** contábil/produto.

**Consolidado em:** [`CHECKLIST_IMPLEMENTACAO_MVP_POS_DOCKER_DEV.md`](./CHECKLIST_IMPLEMENTACAO_MVP_POS_DOCKER_DEV.md) §T1.2.

**Referências:** [`PDF_HOMOLOGACAO_CHECKLIST_B1.md`](./PDF_HOMOLOGACAO_CHECKLIST_B1.md) · [`WEASYPRINT_RUNTIME.md`](./WEASYPRINT_RUNTIME.md) · [`DECISOES_PENDENTES_DEV_09052026_V2_RESPOSTA.md`](./DECISOES_PENDENTES_DEV_09052026_V2_RESPOSTA.md) §2 (P5) · [`CHECKLIST_CONFIRMACAO_ALLAN_MVP.md`](./CHECKLIST_CONFIRMACAO_ALLAN_MVP.md) §1 (linha P5 B.2).

---

## Pré-requisitos

- [ ] **T1.1** fechado (mesmo Postgres Docker / paridade de schema — ver [`CHECKLIST_T1_1_MVP_GATE_DOCKER.md`](./CHECKLIST_T1_1_MVP_GATE_DOCKER.md)).
- [ ] Stack local: `make dev` — API `http://127.0.0.1:60000`, Next `60001`, WeasyPrint disponível no contentor da API (não usar stub mascarado como produção).
- [ ] Decisão **quem assina** o sign-off e formato da ata — preencher §2 em [`DECISOES_PENDENTES_DEV_09052026_V2_RESPOSTA.md`](./DECISOES_PENDENTES_DEV_09052026_V2_RESPOSTA.md) (opção A Allan / opção B terceiro).

---

## Passo 1 — Definir os cinco cases (obrigatório)

Marque cada linha quando o **payload** do diagnóstico (empresa + questionário) reflectir o setor.

| # | Macro | Exemplo de perfil | OK |
|---|--------|-------------------|---|
| 1 | **Varejo** | Supermercado, drogaria | [ ] |
| 2 | **Indústria** | Manufatura | [ ] |
| 3 | **Serviços** | Consultoria, TI | [ ] |
| 4 | **Agro** | Produção primária | [ ] |
| 5 | **Saúde** | Clínica, laboratório | [ ] |

**Sugestão:** variar `setor_macro`, `regime`, `porte` e respostas para exercitar blocos dinâmicos (cronograma, matriz, checklist) quando aplicável ao motor atual.

---

## Passo 2 — Gerar cada PDF (fluxo recomendado)

Para **cada** um dos cinco diagnósticos:

1. [ ] Obter JWT da **conta na plataforma** (`POST /auth/login` ou UI em `http://127.0.0.1:60001/login`) — ver Swagger `http://127.0.0.1:60000/docs`.
2. [ ] Concluir o **wizard** até finalizar com aceite LGPD **ou** chamar `POST /diagnosticos/` (JWT da conta na plataforma) com `aceite_termos_privacidade: true`, `Idempotency-Key` (UUID v4), **CNPJ válido** e corpo válido (`IniciarDiagnosticoPainelRequest` — ver ADR-013). Para PDF só via fluxo **OTP** sem conta, usar `POST /diagnosticos/self-service` / rascunho com `IniciarDiagnosticoRequest`.
3. [ ] Confirmar **`201`**, diagnóstico **finalizado**, e campo de relatório PDF (`relatorio_pdf_url` ou fluxo documentado no teu ambiente) **preenchido** após geração WeasyPrint.
4. [ ] **Guardar** o ficheiro `.pdf` com nome estável, ex.:  
   `T1_2_varejo_YYYYMMDD.pdf` … `T1_2_saude_YYYYMMDD.pdf`.

**Armazenamento dos PDFs:** não commits no Git com **dados pessoais reais** não autorizados — usar arquivo interno (drive, ticket, objeto privado) e **referenciar** apenas nomes + localização mascarada no repositório.

---

## Passo 3 — Critérios por PDF (revisão humana)

Para **cada** PDF, confirmar:

- [ ] **M04:** capa; síntese executiva; dimensões; gaps/recomendações.
- [ ] **Blocos dinâmicos:** cronograma (5 fases); matriz de impacto; checklist do plano (quando gerados).
- [ ] **Rodapé / disclaimer:** LC 214/2025, EC 132/2023, ABNT NBR 17301:2026.
- [ ] **PT-BR** e acentuação correctas (`locale_relatorio` típico `pt-BR`).
- [ ] **Locale render:** ambiente com UTF-8 (`WEASYPRINT_RUNTIME.md` — `LANG`/`LC_ALL`).
- [ ] **Síntese executiva:** sem quebra feia (`page-break-inside: avoid` no template homologado).

---

## Passo 4 — Checklist B.2 e B.3 no repositório

1. [ ] Abrir [`PDF_HOMOLOGACAO_CHECKLIST_B1.md`](./PDF_HOMOLOGACAO_CHECKLIST_B1.md).
2. [ ] Secção **Sign-off (B.2):** preencher tabela (contábil/fiscal, produto, **datas**).
3. [ ] Acrescentar subsecção **B.2 — T1.2 (cinco PDFs reais)** com tabela:

| Setor | Ficheiro / ID interno | Data geração | Observações |
|-------|------------------------|--------------|-------------|
| Varejo | | | |
| Indústria | | | |
| Serviços | | | |
| Agro | | | |
| Saúde | | | |

4. [ ] Confirmar checkpoints aplicáveis em [`WEASYPRINT_RUNTIME.md`](./WEASYPRINT_RUNTIME.md) (timeout `QDI_PDF_RENDER_TIMEOUT_SECONDS`, fontes em deploy se diferente do Mac).

---

## Passo 5 — Sign-off formal e confirmações

1. [ ] **Ata ou registo datado** conforme §2 de [`DECISOES_PENDENTES_DEV_09052026_V2_RESPOSTA.md`](./DECISOES_PENDENTES_DEV_09052026_V2_RESPOSTA.md) (quem assina, formato, prazo).
2. [ ] Marcar **[x]** na linha **P5 — PDF sign-off contábil (B.2)** em [`CHECKLIST_CONFIRMACAO_ALLAN_MVP.md`](./CHECKLIST_CONFIRMACAO_ALLAN_MVP.md) §1 (colunas Data / Notas).
3. [ ] Se aplicável P5 B.3 (espelho WeasyPrint = prod): mesma linha ou `RUNBOOK_DEPLOY_ROLLBACK.md` — conforme o teu critério de “paridade”.

---

## Aceite final T1.2

- [ ] Cinco setores obrigatórios cobertos com PDF **real** revisado.
- [ ] Referências e sign-off em `PDF_HOMOLOGACAO_CHECKLIST_B1.md` + decisões §2 actualizadas.
- [ ] `WEASYPRINT_RUNTIME.md` considerado para o ambiente onde geraste os PDFs.
- [ ] Caixas §T1.2 em [`CHECKLIST_IMPLEMENTACAO_MVP_POS_DOCKER_DEV.md`](./CHECKLIST_IMPLEMENTACAO_MVP_POS_DOCKER_DEV.md) assinaladas.

---

## Falhas frequentes

| Sintoma | Acção |
|---------|--------|
| PDF não gera / URL vazia | Logs `qdi-api`; WeasyPrint deps no Dockerfile; storage mock vs real. |
| 401/403 no POST | JWT válido; `Idempotency-Key` presente; tenant correcto. |
| Conteúdo inglês inesperado | `locale_relatorio` no payload (`pt-BR` vs `en`). |

---

**Última revisão:** 2026-05-10.
