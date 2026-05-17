import { describe, expect, it } from "vitest";

import {
  API_PROXY_TIMEOUT_DIAGNOSTICO_MS,
  isProxyRotaDiagnosticoLonga,
  timeoutProxyMsForRequest,
  timeoutProxyMsPadrao,
} from "@/lib/server/api_proxy_timeout";

describe("api_proxy_timeout", () => {
  it("identifica POST /diagnosticos como rota longa", () => {
    expect(isProxyRotaDiagnosticoLonga("POST", "/diagnosticos")).toBe(true);
    expect(isProxyRotaDiagnosticoLonga("POST", "/diagnosticos/")).toBe(true);
    expect(isProxyRotaDiagnosticoLonga("GET", "/diagnosticos")).toBe(false);
    expect(isProxyRotaDiagnosticoLonga("POST", "/diagnosticos/questionario")).toBe(false);
    expect(
      isProxyRotaDiagnosticoLonga(
        "POST",
        "/diagnosticos/d962dd5e-76f2-4af7-914e-f51728216ecc/explicacao-score-llm",
      ),
    ).toBe(true);
  });

  it("timeout de diagnóstico é maior que o padrão", () => {
    expect(timeoutProxyMsForRequest("POST", "/diagnosticos/")).toBeGreaterThanOrEqual(
      timeoutProxyMsPadrao(),
    );
    expect(timeoutProxyMsForRequest("POST", "/diagnosticos/")).toBe(
      API_PROXY_TIMEOUT_DIAGNOSTICO_MS,
    );
  });
});
