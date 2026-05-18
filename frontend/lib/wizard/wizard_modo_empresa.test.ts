import { describe, expect, it } from "vitest";

import {
  buildWizardUrlNovaDiagnosticoEmpresa,
  buildWizardUrlRefazerQuestionarioCiclo,
} from "@/lib/dashboard/empresa_diagnostico_urls";
import {
  buildWizardUrlNovaEmpresa,
  parseWizardModoEmpresaFromSearchParams,
  WIZARD_MODO_NOVO_CICLO,
  WIZARD_MODO_NOVA_EMPRESA,
  WIZARD_MODO_REFAZER_CICLO,
} from "@/lib/wizard/wizard_modo_empresa";

describe("wizard_modo_empresa", () => {
  it("parseWizardModoEmpresaFromSearchParams — novo_ciclo com CNPJ", () => {
    const sp = new URLSearchParams(
      "modo=novo_ciclo&empresa_cnpj=11222333000181&empresa_razao_social=Acme%20SA",
    );
    const out = parseWizardModoEmpresaFromSearchParams(sp);
    expect(out.modo).toBe(WIZARD_MODO_NOVO_CICLO);
    expect(out.cnpj14).toBe("11222333000181");
    expect(out.razaoSocial).toBe("Acme SA");
  });

  it("parseWizardModoEmpresaFromSearchParams — legacy só empresa_cnpj", () => {
    const sp = new URLSearchParams("empresa_cnpj=11222333000181");
    expect(parseWizardModoEmpresaFromSearchParams(sp).modo).toBe(WIZARD_MODO_NOVO_CICLO);
  });

  it("buildWizardUrlNovaEmpresa inclui modo nova_empresa", () => {
    expect(buildWizardUrlNovaEmpresa()).toBe("/wizard?modo=nova_empresa");
  });

  it("buildWizardUrlNovaDiagnosticoEmpresa inclui modo novo_ciclo", () => {
    const url = buildWizardUrlNovaDiagnosticoEmpresa("11222333000181", "Empresa X");
    const sp = new URLSearchParams(url.split("?")[1]);
    expect(sp.get("modo")).toBe(WIZARD_MODO_NOVO_CICLO);
    expect(sp.get("empresa_cnpj")).toBe("11222333000181");
    expect(parseWizardModoEmpresaFromSearchParams(sp).modo).toBe(WIZARD_MODO_NOVO_CICLO);
    expect(parseWizardModoEmpresaFromSearchParams(new URLSearchParams("modo=nova_empresa")).modo).toBe(
      WIZARD_MODO_NOVA_EMPRESA,
    );
  });

  it("buildWizardUrlRefazerQuestionarioCiclo inclui diagnostico_id", () => {
    const did = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee";
    const url = buildWizardUrlRefazerQuestionarioCiclo("11222333000181", "Empresa X", did);
    const sp = new URLSearchParams(url.split("?")[1]);
    expect(sp.get("modo")).toBe(WIZARD_MODO_REFAZER_CICLO);
    expect(sp.get("diagnostico_id")).toBe(did);
    expect(parseWizardModoEmpresaFromSearchParams(sp).modo).toBe(WIZARD_MODO_REFAZER_CICLO);
  });
});
