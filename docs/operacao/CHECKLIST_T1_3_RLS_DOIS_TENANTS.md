# Como fechar T1.3 — Evidência humana RLS dois tenants (Postgres Docker)

**Objetivo:** documentar que, no **mesmo** Postgres do **Docker Compose** que usaste em T1.1 (`127.0.0.1:60322` típico), um utilizador do **tenant B** **não** consegue ler o diagnóstico criado no **tenant A** — critério alinhado a `tests/integration/test_mvp_gate_postgres.py` e `make mvp-gate`, mas com **registo explícito** para auditoria humana.

**Consolidado em:** [`CHECKLIST_IMPLEMENTACAO_MVP_POS_DOCKER_DEV.md`](./CHECKLIST_IMPLEMENTACAO_MVP_POS_DOCKER_DEV.md) §T1.3.

**Referências:** [`EVIDENCIA_RLS_DOIS_TENANTS_TEMPLATE.md`](./EVIDENCIA_RLS_DOIS_TENANTS_TEMPLATE.md) · [`DECISOES_PENDENTES_DEV_09052026_V2_RESPOSTA.md`](./DECISOES_PENDENTES_DEV_09052026_V2_RESPOSTA.md) §3 (P6) · [`CHECKLIST_CONFIRMACAO_ALLAN_MVP.md`](./CHECKLIST_CONFIRMACAO_ALLAN_MVP.md) §1 · Swagger `http://127.0.0.1:60000/docs`.

---

## Pré-requisitos

- [ ] **T1.1** fechado para o mesmo ambiente Postgres Docker (schema + RLS aplicados).
- [ ] `make dev` (ou `docker compose up -d db` + API a apontar para esse Postgres).
- [ ] API acessível em **`http://127.0.0.1:60000`** (porta típica Compose deste repo).

---

## Passo 1 — Paridade automatizada (sanidade rápida)

Opcional mas recomendado antes da evidência manual:

```bash
make mvp-gate
```

- [ ] **Exit 0** — inclui `test_rls_authenticated_ve_apenas_proprio_tenant`.

Isto **não substitui** o preenchimento do template humano (T1.3); confirma que o teu Docker está coerente com CI.

---

## Passo 2 — Obter dois tenants e dois JWTs distintos

O isolamento é por **`tenant_id`** no JWT (`get_current_user_tenant`), não por e-mail isolado.

1. [ ] **Tenant A:** criar conta na plataforma / consultor com login próprio (fluxo `POST /auth/cadastro` + confirmar e-mail conforme ambiente dev, ou usar utilizadores já existentes em dev).
2. [ ] **Tenant B:** repetir com **outro** e-mail — deve resultar em **outro** `tenant_id` no token após login (`POST /auth/login`).
3. [ ] Guardar **fora do Git** (gestor de passwords, nota local) os tokens ou credenciais de teste — **não** colar Bearer completo em ficheiros versionados.

**Dica:** anotar apenas os **prefixos** dos UUIDs `tenant_id` ou hashes truncados no template público, se precisares de rasto sem expor JWT.

---

## Passo 3 — Criar diagnóstico no tenant A

1. [ ] Login como **utilizador do tenant A** → copiar `Authorization: Bearer …`.
2. [ ] `POST /diagnosticos/` com `Idempotency-Key` único e payload válido (wizard completo ou corpo mínimo aceite pela API).
3. [ ] Resposta **`201`** — anotar **`diagnostico_id`** (= `id_A`).
4. [ ] Opcional: `GET /diagnosticos/` com o mesmo JWT → lista deve incluir `id_A`.
5. [ ] Opcional: `GET /diagnosticos/?empresa_cnpj=<CNPJ do payload>` → deve incluir `id_A` quando o diagnóstico foi gravado com esse `empresa_cnpj` (filtro server-side por tenant).

---

## Passo 4 — Tentar leitura cruzada com tenant B

1. [ ] Login como **utilizador do tenant B** → novo Bearer.
2. [ ] `GET /diagnosticos/{id_A}`.

**Resultado esperado (aceite T1.3):**

- [ ] **`404 Not Found`** **ou** comportamento documentado equivalente (ex.: lista vazia em listagens, conforme contrato actual da API).

Se obtiveres **200** com corpo do diagnóstico de outro tenant → **falha de segurança**: não fechar T1.3; investigar RLS/policies e JWT.

---

## Passo 5 — Preencher template de evidência

1. [ ] Abrir [`EVIDENCIA_RLS_DOIS_TENANTS_TEMPLATE.md`](./EVIDENCIA_RLS_DOIS_TENANTS_TEMPLATE.md).
2. [ ] Preencher **data**, **executor**, menção explícita **«Postgres Docker Compose — 127.0.0.1:60322»** (ou host/porta efectivos **sem** passwords).
3. [ ] Descrever **Passos** 1–4 em texto curto (tenant A/B, `id_A` mascarado se necessário).
4. [ ] Marcar **[x] Isolamento confirmado**.
5. [ ] **Artefacto:** screenshot da resposta **404** (Swagger/cURL) **ou** log redigido **sem** JWT — pode ser anexo interno; no Git, manter só descrição.

---

## Passo 6 — Checklist consolidado Allan (sem secrets)

1. [ ] Em [`CHECKLIST_CONFIRMACAO_ALLAN_MVP.md`](./CHECKLIST_CONFIRMACAO_ALLAN_MVP.md) §1: na linha **P6 — RLS smoke dois tenants** em Postgres Docker (já coberta por `make mvp-gate`), **actualizar a coluna Notas** com data e referência **«evidência humana T1.3 — `EVIDENCIA_RLS_DOIS_TENANTS_TEMPLATE.md`»** (o automatizado permanece; isto acrescenta o registo operacional).
2. [ ] Em [`DECISOES_PENDENTES_DEV_09052026_V2_RESPOSTA.md`](./DECISOES_PENDENTES_DEV_09052026_V2_RESPOSTA.md) §3: marcar decisão / executor / tenants **mascarados** conforme formulário P6.

---

## Passo 7 — Opcional G3 (cloud)

- [ ] Repetir passos 3–5 contra **projeto Supabase gerido** (segunda evidência, sem service_role keys no Git).

---

## Aceite final T1.3

- [ ] Template `EVIDENCIA_RLS_DOIS_TENANTS_TEMPLATE.md` preenchido com referência ao Postgres Docker local.
- [ ] Nota ou captura em [`CHECKLIST_CONFIRMACAO_ALLAN_MVP.md`](./CHECKLIST_CONFIRMACAO_ALLAN_MVP.md) **sem** JWT real no repositório.
- [ ] Caixa «Isolamento confirmado» no template **[x]**.
- [ ] Caixas §T1.3 em [`CHECKLIST_IMPLEMENTACAO_MVP_POS_DOCKER_DEV.md`](./CHECKLIST_IMPLEMENTACAO_MVP_POS_DOCKER_DEV.md) assinaladas.

---

## Falhas frequentes

| Sintoma | Acção |
|---------|--------|
| Mesmo `tenant_id` nos dois logins | Cadastro criou mesmo tenant — usar segundo cadastro independente ou convite multi-tenant conforme desenho do produto. |
| 404 também para o owner | `id_A` errado ou JWT expirado — repetir GET com JWT do tenant A. |
| Erro de ligação | `docker compose ps`; Postgres em `60322`; API com `DATABASE_URL` coerente. |

---

**Última revisão:** 2026-05-10.
