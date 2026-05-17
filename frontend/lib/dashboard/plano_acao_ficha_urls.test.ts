import { describe, expect, it } from "vitest";

import {
  buildPlanoAcaoFichaHref,
  buildVoltaEmpresaHref,
  parseFichaSearchParams,
  parsePlanoAcaoIdFromRoute,
} from "@/lib/dashboard/plano_acao_ficha_urls";

describe("plano_acao_ficha_urls", () => {
  it("buildPlanoAcaoFichaHref monta path e query", () => {
    const href = buildPlanoAcaoFichaHref("11222333000181", "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa", {
      diagnosticoId: "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
      razaoSocial: "Empresa X",
    });
    expect(href).toContain("/dashboard/empresas/11222333000181/acao/aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa");
    expect(href).toContain("diagnostico_id=bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb");
    expect(href).toContain("razao_social=");
  });

  it("parsePlanoAcaoIdFromRoute valida UUID", () => {
    expect(parsePlanoAcaoIdFromRoute("not-uuid")).toBeNull();
    expect(parsePlanoAcaoIdFromRoute("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")).toBe(
      "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
    );
  });

  it("parseFichaSearchParams extrai diagnostico_id", () => {
    const sp = new URLSearchParams(
      "diagnostico_id=bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb&razao_social=Acme",
    );
    const out = parseFichaSearchParams(sp);
    expect(out.diagnosticoId).toBe("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb");
    expect(out.razaoSocial).toBe("Acme");
  });

  it("buildVoltaEmpresaHref com hash", () => {
    expect(buildVoltaEmpresaHref("11222333000181", "X", "empresa-kanban-plano-titulo")).toContain(
      "#empresa-kanban-plano-titulo",
    );
  });

  it("buildVoltaEmpresaHref com ficha salva", () => {
    const href = buildVoltaEmpresaHref("11222333000181", "X", "empresa-quadro-implantacao-principal", {
      fichaSalva: true,
    });
    expect(href).toContain("ficha_salva=1");
    expect(href).toContain("#empresa-quadro-implantacao-principal");
  });
});
