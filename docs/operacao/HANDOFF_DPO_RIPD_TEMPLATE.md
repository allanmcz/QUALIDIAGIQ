# Handoff jurídico — DPO, RIPD e alinhamento WORM×LGPD (template)

**Uso:** preencher sem dados pessoais reais; anexar parecer fora do Git se necessário.  
**Ligações:** `ADR-012` · `docs/operacao/RUNBOOK_DIREITOS_TITULAR_RASCUNHO.md` · processo jurídico MVP (ficheiro local `docs/legal/STATUS_JURIDICO_MVP.md` — pasta `docs/legal/` ignorada pelo Git; sincronizar cópia conforme política interna).

---

## J1 — Encarregado (DPO)

| Campo | Valor (preencher) |
|-------|-------------------|
| Nome completo | _a definir_ |
| E-mail institucional público | _a definir_ |
| Telefone opcional | _a definir_ |
| Data de publicação em `/privacidade` | _a definir_ |

## J2 — RIPD versão 0.1 (estrutura)

1. **Processo:** diagnóstico tributário automatizado (wizard + API + relatório).  
2. **Finalidade:** avaliação de maturidade / lead qualificado / prestação de serviço conforme contrato.  
3. **Bases legais:** execução de contrato; legítimo interesse (avaliar equilíbrio); consentimento onde marcado no fluxo.  
4. **Dados tratados:** categorias (identificação, fiscal, respostas ao questionário, evidências de score).  
5. **Retenção:** prazo por tipo de dado + critério de eliminação/anonimização — **alinhar com ADR-012**.  
6. **Medidas de segurança:** RLS, trilhas de auditoria, WORM em diagnósticos finalizados.  
7. **Riscos e mitigação:** conflito WORM × direito de eliminação → política de anonimização.  
8. **Fluxos internacionais:** _N/A ou descrever_

## J3 — Política de privacidade / termos (checklist revisão)

- [ ] Canal do titular (e-mail DPO) visível em `/privacidade`.  
- [ ] Menção explícita aos fluxos **com** e **sem** conta na plataforma.  
- [ ] Retenção coerente com RIPD.  
- [ ] Versão e data no rodapé ou página dedicada.

## J4 — Workshop WORM × anonimização × eliminação (ata curta)

**Data:** ____ · **Participantes:** ____

**Decisões:**

- Eliminação física permitida em quais estados? (`rascunho` / `em_andamento` / …)  
- Em `finalizado`: apenas anonimização? quais campos?  
- Prazo máximo de resposta a pedidos art. 18:

**Próximos passos:**

- Atualizar `ADR-012` tabela “Decisões em aberto”.  
- Abrir tarefas engenharia quando aplicável.
