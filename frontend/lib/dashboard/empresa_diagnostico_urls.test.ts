import { describe, expect, it } from "vitest";

import {
  buildEmpresaDiagnosticosHref,
  parseCnpjFromRouteSegment,
} from "./empresa_diagnostico_urls";

describe("parseCnpjFromRouteSegment", () => {
  it("extrai CNPJ de segmento simples", () => {
    expect(parseCnpjFromRouteSegment("12345678000195")).toBe("12345678000195");
  });

  it("não rebenta com sequência % ilegal no segmento (evita 500 no servidor)", () => {
    /** decodeURIComponent falharia aqui — fallback mantém dígitos se existirem */
    expect(parseCnpjFromRouteSegment("%ZZ")).toBeNull();
  });
});

describe("buildEmpresaDiagnosticosHref", () => {
  it("inclui query quando razão tem comprimento suficiente", () => {
    const h = buildEmpresaDiagnosticosHref(
      "12345678000195",
      "Empresa Demonstração LTDA",
    );
    expect(h).toContain("/dashboard/empresas/12345678000195");
    expect(h).toContain("razao_social=");
  });
});
