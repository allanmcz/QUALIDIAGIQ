import { afterEach, describe, expect, it, vi } from "vitest";

import { getRetencaoResumoPublicacao } from "./dpoPublic";

describe("getRetencaoResumoPublicacao", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("retorna null quando variável ausente ou vazia", () => {
    vi.stubEnv("NEXT_PUBLIC_LGPD_RETENCAO_RESUMO", "");
    expect(getRetencaoResumoPublicacao()).toBeNull();
  });

  it("retorna texto após trim quando definido", () => {
    vi.stubEnv(
      "NEXT_PUBLIC_LGPD_RETENCAO_RESUMO",
      "  Diagnósticos finalizados: retenção X anos.  ",
    );
    expect(getRetencaoResumoPublicacao()).toBe("Diagnósticos finalizados: retenção X anos.");
  });
});
