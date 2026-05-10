# Runbook — operações sensíveis (direitos do titular LGPD) — **rascunho**

**Estado:** pré-ADR jurídico · não executar exclusões/anonimização em produção sem **ADR-012** fechado e ordem formal.

**Base legal:** Lei **13.709/2018** (arts. **18**, **16**, **46**).

## 1. Quem pode solicitar

| Perfil | Hipótese | Verificação mínima (desenho) |
|--------|----------|------------------------------|
| Utilizador com **sessão na plataforma** | Diagnóstico no **mesmo tenant** | JWT + RLS |
| **Respondente self-service** | E-mail verificado no fluxo OTP/rascunho | Token opaco + correspondência com registo na BD |
| **Representante PJ** | Procuração / contrato | **Definir com jurídico** — não automatizar sem regra escrita |

## 2. Como se prova tenant + vínculo com o diagnóstico

1. Identificar `tenant_id` e `diagnostico_id`.  
2. Para painel: claim JWT deve permitir `SELECT` na linha (RLS).  
3. Para self-service: validar `respondente_email` / tokens de leitura conforme rotas existentes (`conclusao-visualizacao`, etc.).  
4. **Registar** pedido na tabela `qdi.lgpd_titular_solicitacao` (migração **0028**) via rotas Bearer documentadas em §7 abaixo — **log estruturado**/trace para auditoria; fluxo jurídico completo em ADR-012.

## 3. O que é exportável (portabilidade / acesso)

- **JSON** versionado (`schema_id`: `qdi-diagnostico-export-v1`) — ver `docs/schemas/qdi-diagnostico-export-v1.schema.json`.  
- **PDF** de portabilidade com anexo embutido `qdi-diagnostico-export-v1.json` (pacote único — ADR-012 §4).  
- **Não** incluir dados de outros titulares nem tenants; export só após solicitação tipo **portabilidade** **deferida** e diagnóstico **finalizado** com hash de evidência.

## 4. O que é imutável por WORM e como anonimizar em vez de apagar

- Após `status = finalizado`, mutações em campos de evidência são bloqueadas por triggers (`0005`, `0006`, `0012`, … — ver ADR-012).  
- **Eliminação física** da linha pode ser **inviável** sem dispensa legal.  
- **Anonimização:** sobrescrever PII (nome, e-mail, telefone, razão social se política permitir) com placeholders **apenas** se ADR + migração autorizarem colunas específicas **sem** quebrar integridade referencial ou obrigações fiscais.

## 5. Prazos internos (SLA)

| Etapa | SLA proposto (ajustar com negócio) |
|-------|-----------------------------------|
| Ack do pedido | 48 h úteis |
| Resposta simples (acesso/export) | 15 dias úteis (referência art. 18) |
| Casos complexos / anonimização | Definir com DPO |

## 6. Escalação

1. Suporte interno valida identidade.  
2. **DPO** decide casos limítrofes WORM × eliminação.  
3. Engenharia executa apenas scripts/runbooks **aprovados** e **com backup**.

## 7. API técnica (MVP de enfileiramento — sessão painel)

Requer **Bearer JWT** do tenant. **`Idempotency-Key`** obrigatória nos `POST` indicados. Detalhes: OpenAPI tag **Privacidade (LGPD)** e **Diagnósticos** no `/docs`.

| Método | Caminho | Notas |
|--------|---------|--------|
| `POST` | `/privacidade/solicitacoes` | Cria pedido (tipo, canal, texto); **Idempotency-Key** |
| `GET` | `/privacidade/solicitacoes` | Lista; query opcional `?status=` |
| `PATCH` | `/privacidade/solicitacoes/{id}/status` | Atualiza estado operacional da solicitação |
| `POST` | `/privacidade/diagnosticos/{id}/anonimizar-respondente` | Execução técnica após anonimização **deferida** |
| `GET` | `/privacidade/diagnosticos/{id}/export-portabilidade` | Query `solicitacao_id` + `formato=json` ou `pacote_pdf` |
| `GET` | `/diagnosticos/{id}/retificacoes` | Cadeia append-only (sem UPDATE no diagnóstico original) |
| `POST` | `/diagnosticos/{id}/retificacao` | Nova retificação; **Idempotency-Key** obrigatória |

**Testes de contrato:** `tests/integration/test_privacidade_api.py`, `tests/integration/test_diagnostico_retificacao_api.py` (CI via `make test`). **OpenAPI:** paths mínimos LGPD + retificações em `tests/unit/presentation/test_openapi_generated_contract.py`. **E2E painel (mock API):** `frontend/e2e/dashboard-privacidade-export.spec.ts` (`npm run test:e2e` no diretório `frontend/`).

---

**Referências:** `ADR-012` · `PLANO_HANDOFF_JANELA_23H_LGPD_PWA.md` §6  
