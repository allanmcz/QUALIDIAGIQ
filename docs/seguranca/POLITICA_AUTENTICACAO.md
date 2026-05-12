# Política de autenticação — QualiDiagIQ (MVP)

> Rascunho técnico para alinhar segurança operacional e pentest. Complementa **ADR-004** (sessão HttpOnly roadmap) e **ADR-009** (segredo JWT em produção).

## Modelos suportados

1. **Painel (consultores):** JWT Bearer emitido pela API (`POST /auth/login`), hoje persistido no browser em **`localStorage`** (risco XSS residual — ver ADR-004 / ADR-020).
2. **Self-service:** fluxos OTP + tokens de curta duração conforme routers `/auth/*` e `/diagnosticos/*` (regra de produto em `.cursor/rules/qdi-gravacao-diagnostico-email.mdc`).

## Controlo de acesso

- **`tenant_id`** derivado de claims JWT — nunca de header HTTP solto (anti-padrão S-04).
- **Cadastro público** na plataforma em produção: opt-in explícito `QDI_CADASTRO_CONSULTOR_B2B_HABILITADO` (QDI-H-035).
- **Admins:** `bcrypt` com rounds conforme **ADR-008**; endpoints de manutenção protegidos por dependências de admin.

## Rotação e incidentes

- Comprometer JWT ou segredo: seguir `docs/operacao/RUNBOOK_SEGREDO_VAZADO.md`.
- MFA e lockout avançados: roadmap pós-MVP (Onda 1.1).

## Referências

- LC 214/2025 — previsibilidade e boa fé (contexto reforma).
- Lei 13.709/2018 — medidas técnicas de segurança (art. 46, art. 48).
