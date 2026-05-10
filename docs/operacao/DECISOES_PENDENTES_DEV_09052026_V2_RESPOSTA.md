# Decisões pendentes — DEV_09052026_V2

> Formulário executivo para fechar pendências T1–T4 antes da próxima rodada de operação, compliance e produto.
>
> Fontes consultadas: `_DEVELOPER/DEV_09052026_V2/BACKLOG_TAREFAS_T1_T4.md`, `.github/adr/ADR-012-lgpd-worm-direitos-titular.md`, `docs/operacao/HANDOFF_DPO_RIPD_TEMPLATE.md`, `docs/legal/STATUS_JURIDICO_MVP.md`.
>
> Observação: `PLANO_PROXIMOS_PASSOS_2026-05-10.md` não foi localizado neste clone.
>
> Checklist operacional consolidado (marcar progresso): [CHECKLIST_IMPLEMENTACAO_MVP_POS_DOCKER_DEV.md](./CHECKLIST_IMPLEMENTACAO_MVP_POS_DOCKER_DEV.md).

## O que precisa de decisão sua (Allan)

1. Confirmar que T1.1 corre contra **Postgres Docker Compose** (`make dev`) e quando rodar o `make mvp-gate` (cloud opcional antes do go-live público — ver secção 1).
2. Definir quem assina o sign-off contábil dos 5 PDFs reais da T1.2.
3. Confirmar formato de evidência RLS **Docker local** para T1.3 (staging cloud opcional antes do go-live público).
4. Assinar MUST 12/12 T1.4, com data e exceções residuais explícitas.
5. Agendar workshop J4 e fechar decisões WORM × anonimização × eliminação.
6. Designar DPO e dados públicos para `/privacidade`.
7. Nomear responsável e prazo para RIPD v0.1.
8. Confirmar prazos finais de retenção versus baseline da ADR-012.
9. Validar versão/vigência publicada em `/privacidade` via env.
10. Priorizar M08 antes de qualquer SHOULD ou registrar exceção.
11. Indicar bloqueios que impeçam commit automático.

---

## 1. Ambiente Docker Compose (dev) — T1.1 (+ cloud opcional)

**Objetivo:** decidir quando executar `make mvp-gate` e `make verify-schema-mvp-strict` nesta rodada, usando **Postgres do Docker Compose** como baseline no desenvolvimento (sem versionar passwords em repo). **Supabase cloud** pode ser segunda evidência antes do go-live público.

- [ ] Decisão tomada
- **Data da decisão:** ____/____/______
- **Responsável por executar:** ______________________________
- **Janela prevista para T1.1:** ____/____/______ às ______
- **Stack:** `make dev` ou `docker compose up -d`
- **Postgres host/porta típicos:** `127.0.0.1` / `60322` (serviço `db` no `docker-compose.yml`)
- **Variável de conexão usada:** `QDI_POSTGRES_TEST_URL` (ex.: `postgresql://postgres:postgres@127.0.0.1:60322/postgres` — não versionar secrets em artefactos públicos)
- **URL API local (quando compose completo):** ______________________________ (ex.: `http://127.0.0.1:60000`)
- **Projeto Supabase gerido — URL/host (opcional, segunda evidência pré-go-live):** ______________________________
- **Local seguro onde segredos cloud ficarão armazenados (se aplicável):** ______________________________

**Opções:**

- [ ] **A — Baseline MVP via Docker Compose:** executar T1.1 com `QDI_POSTGRES_TEST_URL` apontando ao Postgres do compose local (ver `docs/operacao/EXECUCAO_DEV_09052026_V2_CHECKLIST_OPS.md`).
- [ ] **B — Segunda evidência Supabase cloud:** repetir o mesmo gate num projeto Supabase gerido antes do go-live público (registar data e executor).
- [ ] **C — Adiar execução:** manter apenas evidência CI/regressão até nova janela (documentar data-limite).

**Critério de aceite escolhido:**

________________________________________________________________________________

**Notas:**

________________________________________________________________________________

---

## 2. P5 — Sign-off contábil dos 5 PDFs reais — T1.2

**Objetivo:** definir quem aprova os 5 PDFs reais dos setores de calibração: varejo, indústria, serviços, agro e saúde.

- [ ] Decisão tomada
- **Data da decisão:** ____/____/______
- **Quem assina o sign-off:** ______________________________
- **Cargo/função:** ______________________________
- **Formato da ata:** ______________________________
- **Data-limite para conclusão dos 5 PDFs:** ____/____/______

**Opções:**

- [ ] **A — Allan assina como produto/controlador:** ata datada anexada ao checklist operacional.
- [ ] **B — Validação por terceiro contábil/jurídico:** ata assinada por responsável externo ou consultor designado.

**Exceções ou ressalvas por setor:**

________________________________________________________________________________

**Notas:**

________________________________________________________________________________

---

## 3. P6 — Evidência RLS (Postgres Docker local) — T1.3

**Objetivo:** confirmar evidência mínima de isolamento multi-tenant no **Postgres do Docker Compose**: tenant B não acessa diagnóstico do tenant A (mesmo critério que smoke em CI). Opcionalmente repetir em Supabase cloud antes do go-live público.

- [ ] Decisão tomada
- **Data da decisão:** ____/____/______
- **Executor:** ______________________________
- **Ambiente:** Postgres Docker Compose (`127.0.0.1:60322` típico) / opcional cloud: ______________________________
- **Tenants de teste:** Tenant A __________________ / Tenant B __________________
- **Template de evidência:** `docs/operacao/EVIDENCIA_RLS_DOIS_TENANTS_TEMPLATE.md`

**Opções:**

- [ ] **A — Evidência via API:** `GET /diagnosticos/{id_A}` com JWT do tenant B retorna 404 ou lista vazia.
- [ ] **B — Evidência via API + SQL controlado:** incluir validação adicional com sessão/claim simulada em SQL, sem expor segredos.

**Artefato anexado:**

________________________________________________________________________________

**Notas:**

________________________________________________________________________________

---

## 4. MUST 12/12 e declaração de corte — T1.4

**Objetivo:** assinar `MVP_CRITERIO_CORTE_E_DECLARACAO_MUST.md` com ACT-K01 e ACT-K03 depois de T1.1, T1.2 e T1.3.

- [ ] Decisão tomada
- **Data da assinatura:** ____/____/______
- **Assinante:** ______________________________
- **Documento atualizado:** `docs/operacao/MVP_CRITERIO_CORTE_E_DECLARACAO_MUST.md`

**Opções:**

- [ ] **A — MUST 12/12 fechado:** todos os MUST estão funcionais e com auditabilidade mínima.
- [ ] **B — MUST 12/12 com exceções residuais:** lançar apenas com exceções explicitamente datadas.

**Exceções residuais, se houver:**

1. ______________________________________________________________________________
2. ______________________________________________________________________________
3. ______________________________________________________________________________

**O que fica fora do lançamento e vai para Beta/SHOULD:**

________________________________________________________________________________

---

## 5. Workshop J4 — WORM × anonimização × eliminação

**Objetivo:** fechar as decisões que destravam RIPD v0.1 e retenção final da ADR-012.

- [ ] Decisão tomada
- **Data do workshop:** ____/____/______
- **Horário:** ______ às ______
- **Participantes:** ___________________________________________________________
- **Ata atualizada em:** `docs/operacao/HANDOFF_DPO_RIPD_TEMPLATE.md` §J4

**Decisão 1 — eliminação física permitida em quais estados?**

- [ ] **A — Apenas `rascunho` e `em_andamento` sem WORM ativo.**
- [ ] **B — Nenhum estado permite eliminação física; usar anonimização ou retenção fundamentada.**
- [ ] **Outro:** _______________________________________________________________

**Decisão 2 — diagnóstico `finalizado`: quais campos anonimizam?**

- [ ] **A — Nome, e-mail, telefone e IP de origem; preservar núcleo técnico auditável.**
- [ ] **B — Lista distinta definida pelo DPO/controlador.**
- **Campos finais:** ___________________________________________________________

**Decisão 3 — prazo de resposta a pedidos LGPD art. 18:**

- [ ] **A — 15 dias úteis, alinhado ao prazo de declaração clara e completa da LGPD art. 19, II.**
- [ ] **B — 7 dias como boa prática interna.**
- [ ] **Outro SLA:** ___________________________________________________________

**Notas:**

________________________________________________________________________________

---

## 6. DPO — nome, canal e publicação

**Objetivo:** formalizar Encarregado de Proteção de Dados, canal público e data de publicação em `/privacidade`.

- [ ] Decisão tomada
- **Data da decisão:** ____/____/______
- **Nome completo do DPO:** ______________________________
- **E-mail institucional público:** ______________________________
- **Telefone público/opcional:** ______________________________
- **Data de publicação em `/privacidade`:** ____/____/______
- **Acumulação provisória por Allan no MVP?** Sim ____ / Não ____

**Opções:**

- [ ] **A — Allan acumula provisoriamente no MVP:** registrar substituição planejada quando houver tração comercial.
- [ ] **B — DPO externo ou responsável designado:** publicar nome/canal institucional já no lançamento.

**Variáveis/env relacionadas:**

- `NEXT_PUBLIC_LGPD_DPO_EMAIL`: ______________________________
- `NEXT_PUBLIC_LGPD_DPO_NOME`: ______________________________

**Notas:**

________________________________________________________________________________

---

## 7. RIPD v0.1 — responsável e prazo

**Objetivo:** indicar responsável por redigir/revisar o RIPD, conforme LGPD art. 38, sem inserir dados pessoais desnecessários no Git.

- [ ] Decisão tomada
- **Data da decisão:** ____/____/______
- **Responsável pela minuta:** ______________________________
- **Responsável pela aprovação:** ______________________________
- **Prazo da versão 0.1:** ____/____/______
- **Local do registro versionado:** ______________________________

**Opções:**

- [ ] **A — RIPD resumido no template operacional:** preencher `docs/operacao/HANDOFF_DPO_RIPD_TEMPLATE.md` §J2.
- [ ] **B — RIPD em documento jurídico separado:** registrar apenas status e referência em `docs/legal/STATUS_JURIDICO_MVP.md`.

**Oito pontos mínimos confirmados:**

- [ ] Processo
- [ ] Finalidade
- [ ] Bases legais
- [ ] Dados tratados
- [ ] Retenção
- [ ] Medidas de segurança
- [ ] Riscos e mitigação
- [ ] Fluxos internacionais

**Notas:**

________________________________________________________________________________

---

## 8. Retenção final versus baseline ADR-012

**Objetivo:** confirmar se o baseline operacional vira decisão final de retenção ou se será ajustado após J4/RIPD.

- [ ] Decisão tomada
- **Data da decisão:** ____/____/______
- **Responsável pela aprovação:** ______________________________
- **Documento que refletirá a decisão:** `.github/adr/ADR-012-lgpd-worm-direitos-titular.md`

**Baseline atual a confirmar:**

| Categoria | Baseline atual | Prazo final aprovado |
|-----------|----------------|----------------------|
| Diagnóstico finalizado (hash + conteúdo técnico) | 5 anos | __________________ |
| Dados pessoais do titular após cancelamento | cancelamento + 6 meses | __________________ |
| Logs de auditoria multi-tenant | 5 anos | __________________ |

**Opções:**

- [ ] **A — Confirmar baseline atual:** espelhar no RIPD e na política publicada.
- [ ] **B — Ajustar prazos:** registrar fundamento jurídico e prazo final por categoria antes de automatizar retenção.

**Notas/fundamento:**

________________________________________________________________________________

---

## 9. Revisão `/privacidade` — versão, vigência e env

**Objetivo:** validar que a página pública mantém coerência com operação real, DPO, retenção e fluxos com/sem conta na plataforma.

- [ ] Decisão tomada
- **Data da decisão:** ____/____/______
- **Versão publicada:** ______________________________
- **Vigência publicada:** ____/____/______
- **Ambiente:** Staging ____ / Produção ____

**Checklist mínimo:**

- [ ] Canal do titular com e-mail DPO visível em `/privacidade#dpo`.
- [ ] Menção explícita aos fluxos com e sem conta na plataforma.
- [ ] Retenção coerente com RIPD e ADR-012.
- [ ] Versão e data no rodapé ou área própria.

**Variáveis/env relacionadas:**

- `NEXT_PUBLIC_POLITICA_PRIVACIDADE_VERSAO`: ______________________________
- `NEXT_PUBLIC_POLITICA_PRIVACIDADE_VIGENCIA`: ______________________________
- `NEXT_PUBLIC_LGPD_DPO_EMAIL`: ______________________________

**Opções:**

- [ ] **A — Publicar versão/vigência via env no MVP.**
- [ ] **B — Manter versão apenas em changelog interno por enquanto.**

**Notas:**

________________________________________________________________________________

---

## 10. Prioridade M08 versus outros SHOULD — T4.1

**Objetivo:** confirmar se M08, ancoragem legal por bullet, abre antes de qualquer SHOULD, preservando o critério MUST 12/12.

- [ ] Decisão tomada
- **Data da decisão:** ____/____/______
- **Branch sugerida se aprovada:** `feat/qdi-domain-m08-ancoragem-legal`
- **Data estimada de início:** ____/____/______

**Opções:**

- [ ] **A — M08 antes dos SHOULD:** só abrir S01, S05 ou outros SHOULD após M08 definido/planejado.
- [ ] **B — Antecipar SHOULD específico:** registrar exceção, motivo e impacto no critério de lançamento.

**SHOULD antecipado, se houver:**

________________________________________________________________________________

**Justificativa da prioridade/exceção:**

________________________________________________________________________________

---

## 11. Bloqueios que impedem commit automático

**Objetivo:** registrar situações em que o agente não deve criar commit, mesmo que a documentação esteja pronta.

- [ ] Decisão tomada
- **Data da decisão:** ____/____/______

**Bloqueios atuais ou esperados:**

- [ ] Há alterações pendentes de Allan no workspace.
- [ ] Há arquivos jurídicos com dados pessoais reais que não devem ir para Git.
- [ ] Há segredos/env/URLs sensíveis no diff.
- [ ] Há decisão de produto ainda não preenchida neste formulário.
- [ ] O commit deve ser feito manualmente após revisão.
- [ ] Outro bloqueio: _________________________________________________________

**Opções:**

- [ ] **A — Sem commit automático:** agente apenas cria/atualiza documentação.
- [ ] **B — Commit permitido após workspace limpo:** usar `docs(qdi-docs): adicionar formulário de decisões DEV_09052026_V2`.

**Notas:**

________________________________________________________________________________

---

Como usar: preencher no editor, opcionalmente copiar para PR/comentário.
