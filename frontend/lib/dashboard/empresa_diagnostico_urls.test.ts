import { describe, expect, it } from "vitest";

import {
  buildEmpresaDiagnosticosHref,
  buildEmpresaHrefCiclo,
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

  it("expande ciclo com query expand", () => {
    const h = buildEmpresaHrefCiclo("12345678000195", "Acme", "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa");
    expect(h).toContain("expand=aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa");
  });
});
