import { describe, expect, it } from "vitest";

import type { DiagnosticoResumoApi } from "@/lib/api/lista_diagnosticos";
import {
  agruparEmpresasDeDiagnosticos,
  filtrarEmpresasIndice,
} from "@/lib/painel/privacidade_empresa_indice";

function diag(partial: Partial<DiagnosticoResumoApi>): DiagnosticoResumoApi {
  return {
    id: partial.id ?? "a",
    empresa_razao_social: partial.empresa_razao_social ?? "X",
    empresa_cnpj: partial.empresa_cnpj,
    status: partial.status ?? "finalizado",
    plano: partial.plano ?? "gratuito",
    score_geral: partial.score_geral ?? null,
    criado_em: partial.criado_em ?? "",
    finalizado_em: partial.finalizado_em ?? null,
    relatorio_pdf_url: partial.relatorio_pdf_url ?? null,
  };
}

describe("privacidade_empresa_indice", () => {
  it("agrupa por CNPJ ignorando linhas sem CNPJ 14", () => {
    const empresas = agruparEmpresasDeDiagnosticos([
      diag({ empresa_cnpj: "12345678000190", empresa_razao_social: "ACME" }),
      diag({ empresa_cnpj: "12345678000190", empresa_razao_social: "ACME ATUAL" }),
      diag({ empresa_cnpj: "98765432000110", empresa_razao_social: "BETA" }),
      diag({ empresa_cnpj: "123" }),
    ]);
    expect(empresas).toHaveLength(2);
    expect(empresas.find((e) => e.cnpj14 === "12345678000190")?.razao_social).toBe("ACME ATUAL");
  });

  it("filtra por razão social e CNPJ", () => {
    const empresas = agruparEmpresasDeDiagnosticos([
      diag({ empresa_cnpj: "12345678000190", empresa_razao_social: "ACME COMERCIO" }),
    ]);
    expect(filtrarEmpresasIndice(empresas, "acme")).toHaveLength(1);
    expect(filtrarEmpresasIndice(empresas, "12345678")).toHaveLength(1);
    expect(filtrarEmpresasIndice(empresas, "x")).toHaveLength(0);
  });
});
