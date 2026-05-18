import { describe, expect, it } from "vitest";

import {
  ehChaveQuadroUuid,
  limparSufixoLacunaScoreAcao,
  resolverChaveQuadroSalvar,
  resolverPlanoAcaoIdParaLinha,
} from "@/lib/painel/quadro_implantacao_utils";
import type { PlanoAcaoKanbanCardApi } from "@/types/plano_acao_kanban";

const PLANO_ID = "33333333-3333-4333-a333-333333333331";

describe("limparSufixoLacunaScoreAcao", () => {
  it("remove sufixo legado M07", () => {
    expect(
      limparSufixoLacunaScoreAcao(
        "Parametrizar SPED — lacuna «Contábil» (score 17.9/100).",
      ),
    ).toBe("Parametrizar SPED");
  });
});

describe("resolverChaveQuadroSalvar", () => {
  it("prefere chave do contexto checklist", () => {
    expect(
      resolverChaveQuadroSalvar({
        planoAcaoId: PLANO_ID,
        chaveDeAcaoCtx: "f0_a2",
        chaveQuadroLegado: "f0_a2",
      }),
    ).toBe("f0_a2");
  });

  it("usa plano_acao_id quando checklist não tem contexto", () => {
    expect(
      resolverChaveQuadroSalvar({
        planoAcaoId: PLANO_ID,
        chaveQuadroLegado: "f0_a0",
      }),
    ).toBe(PLANO_ID);
  });

  it("cai no legado do Kanban", () => {
    expect(
      resolverChaveQuadroSalvar({
        planoAcaoId: "x",
        chaveQuadroLegado: "f1_a3",
      }),
    ).toBe("f1_a3");
  });

  it("ehChaveQuadroUuid valida UUID", () => {
    expect(ehChaveQuadroUuid(PLANO_ID)).toBe(true);
    expect(ehChaveQuadroUuid("f0_a1")).toBe(false);
  });
});

describe("resolverPlanoAcaoIdParaLinha", () => {
  const card: PlanoAcaoKanbanCardApi = {
    plano_acao_id: PLANO_ID,
    diagnostico_id: "22222222-2222-4222-a222-222222222222",
    frente_indice: 0,
    frente_nome: "Fiscal",
    acao_indice: 1,
    texto_acao: "Ação teste",
    prioridade_motor: 1,
    chave_quadro_legado: "f0_a1",
    status_execucao: "pendente",
    ordem_kanban: 1,
    arquivado: false,
    comentarios_total: 0,
    subtarefas_total: 0,
  };

  it("resolve pelo plano_acao_id do checklist", () => {
    const id = resolverPlanoAcaoIdParaLinha(
      { descricao: "x", responsavel: "y", prazo: "z", criticidade: "Alta", plano_acao_id: PLANO_ID },
      PLANO_ID,
      {},
    );
    expect(id).toBe(PLANO_ID);
  });

  it("resolve pela chave legado via Kanban quando checklist não traz UUID", () => {
    const id = resolverPlanoAcaoIdParaLinha(
      {
        descricao: "x",
        responsavel: "y",
        prazo: "z",
        criticidade: "Alta",
        chave_quadro_legado: "f0_a1",
      },
      "f0_a1",
      { [PLANO_ID]: card },
    );
    expect(id).toBe(PLANO_ID);
  });
});
