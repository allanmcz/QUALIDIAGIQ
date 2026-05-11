# ADR-013 — CNPJ: opcional no lead (self-service) vs obrigatório no painel (histórico por empresa)

Data: 2026-05-10  
Estado: **aceite** (substitui a regra única «sempre opcional» para POST com conta na plataforma)

## Contexto

O QDI precisa de **dois modos**:

1. **Topo de funil / self-service:** reduzir fricção — o respondente pode concluir o assistente **sem** informar CNPJ e gravar no tenant self-service (rascunho + OTP), conforme fluxo existente.
2. **Conta na plataforma (painel):** garantir **histórico fiável por PJ** no tenant (vários diagnósticos, agrupamento, comparativos “antes/depois”), o que exige identificação cadastral **CNPJ** válido (RFB, DV).

## Decisão

| Contexto | CNPJ | Contrato técnico |
|----------|------|-------------------|
| Rascunho self-service, `POST /diagnosticos/self-service`, conclusão OTP **sem** migrar para tenant consultor | **Opcional** (`""` permitido) | `IniciarDiagnosticoRequest` + `EmpresaSchema` |
| `POST /diagnosticos/` com JWT da **conta na plataforma** | **Obrigatório** (14 dígitos, DV) | `IniciarDiagnosticoPainelRequest` + `EmpresaPainelSchema` |
| `POST /diagnosticos/rascunho-self-service/vincular-conta` | **Obrigatório** no JSON do rascunho | Validação com `IniciarDiagnosticoPainelRequest` sobre o payload persistido |

**Frontend:** `DiagnosticoPayloadSchema` reforça com `superRefine` quando existe `admin_token` no `localStorage` (alinhado ao POST painel).

## Consequências

- Lead sem CNPJ **não** entra no mesmo agrupamento automático “por empresa” até completar CNPJ ou ser recolhido noutro fluxo.
- **LGPD:** titular continua sendo PF; CNPJ é identificação de **PJ** como contexto de negócio — sem mudar a regra de titular.

## Cruzamento

- `.cursor/rules/qdi-cnpj-opcional.mdc` (atualizado para estes dois contextos)
- `.cursor/rules/qdi-gravacao-diagnostico-email.mdc`
