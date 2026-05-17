import { describe, expect, it } from "vitest";

import {
  ehChaveQuadroUuid,
  limparSufixoLacunaScoreAcao,
  resolverChaveQuadroSalvar,
} from "@/lib/painel/quadro_implantacao_utils";

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
