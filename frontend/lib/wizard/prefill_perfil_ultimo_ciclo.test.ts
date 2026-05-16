import { describe, expect, it } from "vitest";

import { mapDetalheParaPerfilEmpresa } from "@/lib/wizard/prefill_perfil_ultimo_ciclo";

describe("mapDetalheParaPerfilEmpresa", () => {
  it("mapeia campos válidos do GET detalhe", () => {
    const r = mapDetalheParaPerfilEmpresa({
      id: "x",
      empresa_razao_social: "ACME",
      plano: "gratuito",
      status: "finalizado",
      relatorio_pdf_url: null,
      checklist: null,
      matriz_impacto: null,
      cronograma: null,
      checklist_m12_autoconf: null,
      versao_otimista: 1,
      score: null,
      empresa_porte: "medio",
      empresa_regime: "lucro_real",
      empresa_cnae: "4711301",
      empresa_uf: "sp",
      empresa_setor_macro: "comercio",
    });
    expect(r).toEqual({
      porte: "medio",
      regime: "lucro_real",
      cnae_principal: "4711301",
      uf: "SP",
      setor_macro: "comercio",
    });
  });

  it("retorna null sem campos reconhecíveis", () => {
    expect(
      mapDetalheParaPerfilEmpresa({
        id: "x",
        empresa_razao_social: "ACME",
        plano: "gratuito",
        status: "finalizado",
        relatorio_pdf_url: null,
        checklist: null,
        matriz_impacto: null,
        cronograma: null,
        checklist_m12_autoconf: null,
        versao_otimista: 1,
        score: null,
      }),
    ).toBeNull();
  });
});
