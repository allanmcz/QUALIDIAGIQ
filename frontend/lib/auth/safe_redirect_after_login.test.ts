import { describe, expect, it } from "vitest";

import { destinoSeguroAposLogin } from "./safe_redirect_after_login";

describe("destinoSeguroAposLogin", () => {
  it("sem redirect devolve lista do painel", () => {
    expect(destinoSeguroAposLogin(null)).toBe("/dashboard/diagnosticos");
    expect(destinoSeguroAposLogin("")).toBe("/dashboard/diagnosticos");
  });

  it("vista por empresa no redirect → lista (não repõe /dashboard/empresas/…)", () => {
    expect(destinoSeguroAposLogin("/dashboard/empresas/12345678000195")).toBe("/dashboard/diagnosticos");
    expect(destinoSeguroAposLogin("/dashboard/empresas/12345678000195?razao_social=x")).toBe(
      "/dashboard/diagnosticos",
    );
  });

  it("mantém ficha de diagnóstico e wizard", () => {
    expect(destinoSeguroAposLogin("/dashboard/diagnosticos/abc-uuid")).toBe("/dashboard/diagnosticos/abc-uuid");
    expect(destinoSeguroAposLogin("/wizard")).toBe("/wizard");
  });
});
