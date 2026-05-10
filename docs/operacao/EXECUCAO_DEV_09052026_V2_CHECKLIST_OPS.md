# Execução DEV_09052026_V2 — checklist operacional

**Data de criação:** 2026-05-10  
**Origem:** `_DEVELOPER/DEV_09052026_V2/BACKLOG_TAREFAS_T1_T4.md` e `PLANO_PROXIMOS_PASSOS_2026-05-10.md`  
**Objetivo:** transformar os bloqueios T1/T2 em passos executáveis sem versionar credenciais, substituindo a execução direta em Supabase cloud nesta sessão.

> Regra operacional: evidências podem conter logs, hashes, screenshots e atas, mas nunca URLs com senha, tokens JWT, service role key, dumps de dados pessoais ou segredos de deploy.

## Pré-voo comum

- [ ] Confirmar branch e hash atual:

```bash
git status --short
git rev-parse --short HEAD
```

- [ ] Confirmar dependências locais antes de gerar evidência:

```bash
make lint
make test
```

- [ ] Se houver alteração front-end no mesmo pacote, executar no diretório `frontend/`:

```bash
npm run lint
```

## T1.1 — `make mvp-gate` em cloud espelho

**Objetivo:** validar o gate automatizado em ambiente que reflita produção, preferencialmente Supabase staging, não apenas Docker Compose local.

**Comandos:**

```bash
export QDI_POSTGRES_TEST_URL="postgresql://...staging.supabase.co:5432/postgres"
export DATABASE_URL="$QDI_POSTGRES_TEST_URL"

make mvp-gate
make verify-schema-mvp-strict
```

**Critérios de aceite:**

- [ ] `make mvp-gate` verde em ambiente cloud espelho.
- [ ] `make verify-schema-mvp-strict` OK usando `QDI_POSTGRES_TEST_URL`.
- [ ] Log datado anexado em `docs/operacao/PDF_HOMOLOGACAO_CHECKLIST_B1.md` ou artefato operacional equivalente.
- [ ] Evidência sem credenciais, host sensível completo ou secrets.

## T1.2 — 5 PDFs reais com sign-off contábil

**Objetivo:** homologar o template M04 em cases reais dos setores de calibração do PRD.

**Cases obrigatórios:**

- [ ] Varejo, preferencialmente supermercado ou drogaria.
- [ ] Indústria, preferencialmente manufatura.
- [ ] Serviços, preferencialmente consultoria ou TI.
- [ ] Agro, preferencialmente produção primária.
- [ ] Saúde, preferencialmente clínica ou laboratório.

**Verificações por PDF:**

- [ ] Marcadores M04 presentes: capa, síntese executiva, dimensões e gaps.
- [ ] Blocos dinâmicos presentes: cronograma 5 fases, matriz de impacto e checklist do plano.
- [ ] Rodapé com disclaimer LC 214/2025, EC 132/2023 e ABNT NBR 17301:2026.
- [ ] Fontes PT-BR com acentuação correta.
- [ ] Locale `pt_BR.UTF-8` ativo no ambiente de render.
- [ ] Quebra de página protegida (`page-break-inside: avoid`) na síntese executiva.

**Critérios de aceite:**

- [ ] 5 PDFs anexados ao checklist B.2 de `docs/operacao/PDF_HOMOLOGACAO_CHECKLIST_B1.md`.
- [ ] Sign-off contábil do Allan formalizado em ata datada.
- [ ] `docs/operacao/WEASYPRINT_RUNTIME.md` cumprido em todos os checkpoints aplicáveis.

## T1.3 — Smoke RLS 2 tenants em Supabase staging

**Objetivo:** evidenciar isolamento multi-tenant em ambiente cloud.

**Passos:**

1. Aplicar migrações até a revisão de produção no ambiente staging.
2. Criar 2 usuários/tenants de teste com JWTs distintos.
3. Inserir diagnóstico no tenant A.
4. Com JWT do tenant B, executar `GET /diagnosticos/{id_A}`.
5. Confirmar retorno `404`, lista vazia ou negativa equivalente documentada.
6. Opcionalmente executar SQL controlado com `SET qdi.jwt_tenant_id` para validar role de serviço.

**Critérios de aceite:**

- [ ] `docs/operacao/EVIDENCIA_RLS_DOIS_TENANTS_TEMPLATE.md` preenchido com data, ambiente e executor.
- [ ] Captura/log anexado em checklist operacional, screenshot SQL ou nota em `docs/operacao/CHECKLIST_CONFIRMACAO_ALLAN_MVP.md`.
- [ ] Caixa "Isolamento confirmado" marcada.
- [ ] Nenhum token JWT real versionado.

## T2.1 — Workshop J4 WORM × anonimização × eliminação

**Objetivo:** fechar as 3 decisões pendentes do `docs/operacao/HANDOFF_DPO_RIPD_TEMPLATE.md` §J4.

**Roteiro de 45 minutos:**

- [ ] 00:00-05:00 — contexto ADR-012 §2: titular PF vs PJ.
- [ ] 05:00-15:00 — decidir quando eliminação física é permitida: `rascunho`, `em_andamento` ou nenhum.
- [ ] 15:00-25:00 — decidir, em diagnóstico `finalizado`, quais campos anonimizam. Sugestão inicial: nome, e-mail, telefone e IP de origem.
- [ ] 25:00-35:00 — decidir SLA de resposta a pedidos art. 18. Opções: 15 dias úteis, 7 dias ou 24h premium.
- [ ] 35:00-45:00 — registrar ata, responsáveis e próximos passos.

**Critérios de aceite:**

- [ ] §J4 preenchido com data, participantes e as 3 decisões nomeadas.
- [ ] ADR-012 atualizado com nota "decidido em workshop" quando a ata estiver fechada.
- [ ] Backlog técnico aberto se a decisão exigir rotina nova de retenção/anonimização.

## T2.2 — Designar DPO

**Objetivo:** formalizar o encarregado de proteção de dados, conforme LGPD art. 41.

**Preencher em `docs/operacao/HANDOFF_DPO_RIPD_TEMPLATE.md` §J1:**

- [ ] Nome completo.
- [ ] E-mail institucional público.
- [ ] Telefone opcional.
- [ ] Data de publicação em `/privacidade`.

**Critérios de aceite:**

- [ ] §J1 preenchido com os 4 campos.
- [ ] Decisão sobre acumulação de função no MVP registrada explicitamente, se aplicável.
- [ ] Deploy front-end com `NEXT_PUBLIC_LGPD_DPO_EMAIL` definido; `NEXT_PUBLIC_LGPD_DPO_NOME` só se houver nome aprovado para publicação.

## T2.3 — RIPD versão 0.1

**Objetivo:** documentar o relatório de impacto do diagnóstico automatizado, conforme LGPD art. 38.

**Estrutura mínima:**

- [ ] Processo: diagnóstico tributário automatizado, wizard, API e relatório PDF.
- [ ] Finalidade: avaliação de maturidade, lead qualificado e prestação de serviço conforme contrato.
- [ ] Bases legais: execução de contrato, legítimo interesse avaliado e consentimento onde marcado no fluxo.
- [ ] Dados tratados: identificação, fiscal, respostas ao questionário e evidências de score.
- [ ] Retenção: diagnóstico finalizado 5 anos; dados pessoais até cancelamento + 6 meses; logs 5 anos.
- [ ] Medidas de segurança: RLS, trilhas de auditoria, WORM em diagnósticos finalizados e testes `tests/integration/test_privacidade_api.py`.
- [ ] Riscos e mitigação: conflito WORM × direito de eliminação; política de anonimização.
- [ ] Fluxos internacionais: N/A ou descrição do provedor/região aplicável.

**Critérios de aceite:**

- [ ] §J2 totalmente preenchido ou parecer/PDF anexo registrado em `docs/legal/STATUS_JURIDICO_MVP.md`.
- [ ] Justificativa explícita de RIPD obrigatório.
- [ ] Documento datado e versionado como v0.1.

## T1.4 — Declaração MUST 12/12 (assinatura humana)

**Objetivo:** assinar formalmente o critério de corte do MVP e a declaração dos 12 MUST.

**Atualizar:** `docs/operacao/MVP_CRITERIO_CORTE_E_DECLARACAO_MUST.md`

**Pré-condições:**

- [ ] T1.1 fechado.
- [ ] T1.2 fechado.
- [ ] T1.3 fechado.

**Conteúdo obrigatório:**

- [ ] ACT-K01: frase de corte declarando o que entra no lançamento e o que fica fora, como Beta/SHOULD.
- [ ] ACT-K03: confirmação de que os 12 MUST do PRD estão atendidos no sentido funcional + auditável mínimo.
- [ ] Exceções residuais com data limite. Se não houver exceção, registrar vazio explícito.
- [ ] Assinatura humana do Allan ou responsável definido.

**Critérios de aceite:**

- [ ] Documento datado e assinado.
- [ ] Exceções residuais explícitas.
- [ ] Hash Git do pacote de evidência registrado.

## T4.1 M08 — próximo sprint engenharia

**Decisão deste passe:** não implementar motor Lexiq completo agora. O objetivo é deixar rastro técnico e critério de aceite para o próximo sprint.

**Rastro no código atual:**

- `src/application/services/lexiq_guardrail.py` — guardrail mínimo Lexiq por regex + RAG opcional, com rejeição quando não há citação válida.
- `tests/unit/application/test_lexiq_guardrail.py` e `tests/unit/application/test_lexiq_guardrail_rag.py` — cobertura do guardrail atual.
- `src/presentation/api/routers/normativa_router.py` — endpoint de checagem heurística, declarado como não substituto do Lexiq/RAG formal.
- `src/application/services/consultoria_service.py` — geração determinística das recomendações iniciais a partir das piores dimensões.
- `src/presentation/api/schemas.py` — resposta atual mantém `recomendacoes_gaps_criticos: list[str]`, ainda sem objeto estruturado com `evidencia_lexiq` por bullet.

**Critério de aceite para M08:**

- [ ] Cada bullet de recomendação tem campo estruturado `evidencia_lexiq` com citação por dispositivo.
- [ ] Citações aceitas incluem LC 214/2025, EC 132/2023, NT 2025.002 v1.33+ e ABNT NBR 17301:2026 quando aplicável.
- [ ] Sem citação válida ou score do retriever abaixo de `0.65`, a API rejeita a recomendação com erro controlado, preferencialmente HTTP 422.
- [ ] Teste unitário rejeita recomendação sem evidência.
- [ ] Cobertura de `src/domain/` permanece em pelo menos 85%.
- [ ] Smoke E2E renderiza PDF com bullets ancorados visualmente.

## Fechamento operacional

- [ ] Atualizar `docs/operacao/ROADMAP_HANDOFF_PROGRESSO_SYNC.md` com data, hash Git e estado real.
- [ ] Registrar no changelog/ata da semana o que ficou manual/cloud.
- [ ] Commitar apenas documentação/copy revisada, sem artefatos sensíveis.
