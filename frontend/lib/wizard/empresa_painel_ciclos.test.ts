import { describe, expect, it, vi } from "vitest";

import { fetchDiagnosticosResumo } from "@/lib/api/lista_diagnosticos";
import { fetchResumoCiclosEmpresaPainel } from "@/lib/wizard/empresa_painel_ciclos";

vi.mock("@/lib/api/lista_diagnosticos", () => ({
  DIAGNOSTICOS_RESUMO_PAGE_SIZE_MAX: 200,
  fetchDiagnosticosResumo: vi.fn(),
}));

describe("empresa_painel_ciclos", () => {
  it("fetchResumoCiclosEmpresaPainel agrega total e próximo NIM", async () => {
    vi.mocked(fetchDiagnosticosResumo).mockResolvedValue([
      {
        id: "a",
        empresa_razao_social: "Acme SA",
        status: "finalizado",
        plano: "gratuito",
        score_geral: 50,
        criado_em: "2026-01-01",
        finalizado_em: "2026-01-02",
        relatorio_pdf_url: null,
        numero_interno_grupo: 2,
      },
      {
        id: "b",
        empresa_razao_social: "Acme SA",
        status: "finalizado",
        plano: "gratuito",
        score_geral: 60,
        criado_em: "2026-02-01",
        finalizado_em: "2026-02-02",
        relatorio_pdf_url: null,
        numero_interno_grupo: 5,
      },
    ]);
    const out = await fetchResumoCiclosEmpresaPainel("11222333000181");
    expect(out.totalCiclos).toBe(2);
    expect(out.proximoNumeroInternoEstimado).toBe(6);
    expect(out.razaoSocialMaisRecente).toBe("Acme SA");
  });
});
