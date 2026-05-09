# Consulta de CNPJ no QualiDiagIQ — decisão operacional + implementação

**Versão:** 2.0 (estado atual no repositório)  
**Datas:** decisão inicial 2026-05-08 · alinhamento pós-implementação 2026-05-08  
**Objetivo:** registar decisões Allan (consulta BrasilAPI → fallback Minha Receita só em erro/timeout), contrato REST, TTL por volatilidade, multi-tenant, WORM/`force_refresh_cnpj`, **migração PostgreSQL**, **uso no frontend** e variáveis de ambiente (`QDI_*`).

> A pasta `_DEVELOPER/CONSULTA_CNPJ` e `_DEVELOPER/CONSULTA_CNPJ_V2` continuam válidas como contexto histórico; **este doc é a fonte de verdade para operação.**

---

## 1. Resumo executivo

- **Consulta cadastral** com persistência por `tenant_id` (JWT), **idempotência** (`Idempotency-Key`), **cache em PostgreSQL com três TTL** (cadastral / qualificação / situação) e encadeamento:
  | Ordem | Fornecedor | Uso |
  |-------|-------------|-----|
  | **1ª** | **BrasilAPI** (`QDI_CNPJ_BRASIL_API_BASE_URL`) | Primeira tentativa sempre que há rede fresca ou refresh. |
  | **2ª** | **Minha Receita** (`QDI_CNPJ_MINHA_RECEITA_URL_TEMPLATE`, placeholder `{cnpj}`) | Só depois de **timeout**, erro de rede, **5xx/429**, ou payload inválido da 1ª — **nunca** apenas por HTTP **404**. |
- **CNPJ opcional** no wizard e na API (`qdi-cnpj-opcional`); quando preenchido, DV RFB válido obrigatório para consultas.
- **Finalização diagnóstico:** corpo pode incluir `force_refresh_cnpj: true` para ignorar TTL e retratar fontes públicas antes do snapshot WORM, com histórico de valores anteriores no servidor (`diagnostico_empresa_campo_historico`).

---

## 2. Migrações PostgreSQL (obrigatório em ambientes existentes)

- **Arquivo:** `src/infrastructure/db/migrations/0030_cnpj_consulta_cache.sql`  
- **Objetos principais:** `cnpj_consultas`, `diagnostico_empresa_campo_historico`, RLS, enum/check de fonte (`brasil_api` \| `minha_receita`).

### Como aplicar (recomendado)

Com ambiente Compose (daemon Docker ativo e serviço `db` erguido):

```bash
make dev    # ou: docker compose up -d db  (+ API se precisar)
make migrate
```

`migrate` reaplica **todas** as migrações em ordem contra o container `db` (`psql` stdin). Para uma base **nova** já inclua `0030` no `init.sql` / pipeline de primeira carga; para base **existente**, execute as migrações pendentes (inclui `0030`) sem recriar o volume.

Sem Docker: use `PostgreSQL_CI_URL` / `DATABASE_URL` e um cliente `psql` apontando para a mesma BD da API (`make ci-integration` é o espelho local do CI).

> **Nota:** se o daemon Docker não está a correr ou a porta `60322` não expõe o Postgres, `make migrate` falha por conectividade — suba o ambiente primeiro.

---

## 3. Contrato API (implementado)

| Item | Definição |
|------|-----------|
| **Rota (aprovado Allan)** | `POST /referencia/cnpj/consulta_cnpj` |
| **Router** | `src/presentation/api/routers/cnpj_router.py` |
| **Auth** | `Authorization: Bearer` com `tenant_id` no JWT (painel ou fluxos com tenant resolvido). |
| **Headers** | `Idempotency-Key` obrigatório neste POST. |
| **Corpo** | `ConsultarCnpjRequest`: `cnpj` (14 dígitos + DV válidos); `force_refresh` boolean; opcional `aplicar_no_diagnostico_id` (merge em diagnóstico **em_andamento**). |

**Fluxo diagnose / rascunho — campo `force_refresh_cnpj`:**  
Mesmo objeto de entrada que `POST /diagnosticos/` / rascunho self-service (`IniciarDiagnosticoRequest` em `schemas.py`). O cliente web envia quando o utilizador marca a opção no último passo do wizard (sessão na plataforma + CNPJ com 14 dígitos).

---

## 4. TTL configurável (`QDI_*`)

Definidas em **`src/infrastructure/config/settings.py`** (Pydantic Settings). Overrides por env (valor em **segundos**):

| Classe de dados (volatilidade) | Variável | Default sugerido (documentado Allan) |
|---------------------------------|----------|--------------------------------------|
| Cadastral (razão social, natureza jurídica, abertura… — anos) | `QDI_CNPJ_TTL_CADASTRAL_SECONDS` | **30 dias** (= 2 592 000 s) |
| Qualificação (CNAE, capital, endereço… — meses) | `QDI_CNPJ_TTL_QUALIFICACAO_SECONDS` | **24 h** (= 86 400 s) |
| Situação cadastral (ativa/suspensa/baixada — overnight) | `QDI_CNPJ_TTL_SITUACAO_SECONDS` | **4 h** (= 14 400 s) |

**Outras env relacionadas:**

- `QDI_CNPJ_BRASIL_API_BASE_URL` — default documentado BrasilAPI.  
- `QDI_CNPJ_MINHA_RECEITA_URL_TEMPLATE` — default inclui `{cnpj}` (substituição dos 14 dígitos).  
- `QDI_CNPJ_HTTP_TIMEOUT_SECONDS` — timeout por chamada HTTP (BrasilAPI / fallback).

---

## 5. Multi-tenant e FK `tenant`

- **`tenant_id` UUID «solto»** (sem FK obrigatória para tabela corporativa única): alinhado ao modelo atual de `diagnosticos.tenant_id` e migrado da mesma forma para `cnpj_consultas` / políticas RLS compatíveis com o restante projeto.

---

## 6. Comportamento de merge no servidor + histórico

- Ao materializar/consultar: **preenche vazios e sobrescreve** quando o valor público diverge do já guardado para a empresa ligada ao diagnóstico.  
- Mantém **`diagnostico_empresa_campo_historico`** com conteúdo anterior e **marcador temporal** conforme DDL `0030` (implementação Postgres em `postgres_diagnostico_repository`).

---

## 7. Fallback Minha Receita (404)

Política aprovada: **não** chamar segunda fonte por 404 só — ver matriz preservada §4 do texto original (`EXPOSICAO` v1) e código em `cnpj_provedor_externo_http`/serviço de consulta.

---

## 8. Frontend (wizard)

Centralizado em:

- **`frontend/lib/api/consulta_cnpj.ts`** — `POST /referencia/cnpj/consulta_cnpj` com Bearer + idempotência.  
- **`frontend/lib/cnpj/canonical_merge.ts`** — aplicação do `canonico` ao `react-hook-form` (porte/regime/setor/CNAE/UF apenas se coincidirem com os enums do Zod local).  
- **Passo 1 — Identificação:** botão «Buscar dados públicos» (requer sessão na plataforma); checkbox opcional para ignorar cache **nessa chamada**.  
- **Último passo do questionário (com JWT + CNPJ 14 dígitos):** checkbox «Opcional: ao finalizar… ignorando cache TTL» ligado ao campo **`force_refresh_cnpj`** no POST de gravar diagnóstico ou rascunho (contrato igual à API Python).

Fluxo sem login continua válido apenas com preenchimento manual + rascunho/OTP ou gravação pós-consultoria — pré-preenchimento via API só com JWT.

---

## 9. LGPD

Inalterados os princípios `_DEVELOPER/CONSULTA_CNPJ/06_LGPD_COMPLIANCE.md` quando existir; uso operacional apenas para qualificação do diagnóstico e minimização em logs (`structlog`; não registar CNPJ completo em texto claro desnecessariamente).

---

## 10. Critérios de aceite — estado

| MUST | Estado |
|------|--------|
| Primeira chamada de rede sempre BrasilAPI (exceto hits de cache válido / idempotência) | Atendido. |
| Minha Receita só em falhas conforme política §4 original | Atendido. |
| Snapshot por tenant + idempotência | Atendido. |
| TTL triplo configurável por env | Atendido. |
| Opção servidor `force_refresh_cnpj` na finalização WORM | Atendido. |
| CNPJ opcional preservado | Atendido. |

---

## 11. Tabela §12 Allan — decidido (implementação)

| # | Questão | Decisão registada |
|---|---------|-------------------|
| 1 | Prefixo da rota REST | **`POST /referencia/cnpj/consulta_cnpj`** |
| 2 | Sobrescrita no wizard/form | **Servidor:** preenche vazios e sobrescreve divergentes **com histórico**; cliente pode pré-visualizar antes com «Buscar dados públicos». |
| 3 | 404 BrasilAPI | **Sem** segunda fonte por 404 apenas. |
| 4 | FK `tenant` | **`tenant_id` UUID** sem novo FK institucional. |
| 5 | TTL default | **Três TTL** por classe de dado (**30d / 24h / 4h**) com override env (§4). |

---

## 12. Referências

- [BrasilAPI — API CNPJ](https://brasilapi.com.br/docs)  
- Minha Receita — URL parametrizável `QDI_CNPJ_MINHA_RECEITA_URL_TEMPLATE`  
- Regras de produto internas: `.cursor/rules/qdi-cnpj-opcional.mdc`, `qdi-gravacao-diagnostico-email.mdc`, `storage-policy`

---

_Approvações anteriores: indicar datas em PR/changelog quando relevante._
