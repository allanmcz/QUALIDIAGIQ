import { describe, expect, it } from "vitest";

import {
  hrefPrivacidadePainel,
  parseSecaoPrivacidade,
} from "@/lib/painel/privacidade_diagnostico_query";

describe("privacidade_diagnostico_query", () => {
  it("monta URL com diagnostico_id e secao", () => {
    const id = "01800000-aaaa-bbbb-cccc-000000000099";
    expect(hrefPrivacidadePainel({ diagnosticoId: id, secao: "lgpd" })).toBe(
      `/dashboard/privacidade?diagnostico_id=${id}&secao=lgpd`,
    );
  });

  it("parseSecaoPrivacidade aceita lgpd e retificacoes", () => {
    expect(parseSecaoPrivacidade("lgpd")).toBe("lgpd");
    expect(parseSecaoPrivacidade("retificacoes")).toBe("retificacoes");
    expect(parseSecaoPrivacidade("outro")).toBeNull();
  });
});
