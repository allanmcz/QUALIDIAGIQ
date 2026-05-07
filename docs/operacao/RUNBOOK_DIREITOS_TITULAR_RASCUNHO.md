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

- Snapshot estruturado do diagnóstico (**JSON**) — campos definidos após legal.  
- **PDF** já gerado, se existir URL ou blob seguro.  
- **Não** incluir dados de outros titulares nem tenants.

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

Requer **Bearer JWT** do tenant e header **`Idempotency-Key`** no `POST`. Detalhes de OpenAPI: tag **Privacidade (LGPD)** no `/docs`.

| Método | Caminho | Notas |
|--------|---------|--------|
| `POST` | `/privacidade/solicitacoes` | Cria pedido (tipo, canal, texto); idempotência por chave |
| `GET` | `/privacidade/solicitacoes` | Lista; query opcional `?status=` |
| `PATCH` | `/privacidade/solicitacoes/{id}/status` | Atualiza estado operacional da solicitação |

**Testes de contrato:** `tests/integration/test_privacidade_api.py` (CI via `make test`).

---

**Referências:** `ADR-012` · `PLANO_HANDOFF_JANELA_23H_LGPD_PWA.md` §6  
