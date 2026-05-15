import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  getExplicacaoScoreLlmHistorico,
  novaIdempotencyKeyExplicacaoScore,
  postExplicacaoScoreLlm,
} from "./explicacao_score_llm";

vi.mock("./config", () => ({
  getApiUrlForFetch: () => "http://api.test",
  cabecalhosAuthPainelOpcional: () => ({ Authorization: "Bearer tok" }),
  temSessaoPainelParaApiCliente: () => true,
}));

vi.mock("@/lib/auth/painel_session", () => ({
  encerrarSessaoPainelSe401: () => false,
}));

describe("postExplicacaoScoreLlm", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({
          text: "Narrativa.",
          provider: "fake",
          model: "m",
          policy_version: "v1",
          input_tokens: 1,
          output_tokens: 2,
          estimated_cost_usd: 0,
          latency_ms: 10,
          blocked_by_guardrail: false,
          guardrail_reason: null,
          guardrail_status: "ok",
        }),
      }),
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.clearAllMocks();
  });

  it("envia POST com Idempotency-Key no path do painel", async () => {
    const id = "550e8400-e29b-41d4-a716-446655440000";
    const key = "chave-fixa-teste";
    await postExplicacaoScoreLlm(id, key);
    expect(fetch).toHaveBeenCalledWith(
      `http://api.test/diagnosticos/${id}/explicacao-score-llm`,
      expect.objectContaining({
        method: "POST",
        headers: expect.objectContaining({
          "Idempotency-Key": key,
          Authorization: "Bearer tok",
        }),
      }),
    );
  });

  it("novaIdempotencyKeyExplicacaoScore gera string não vazia", () => {
    const k = novaIdempotencyKeyExplicacaoScore();
    expect(k.length).toBeGreaterThan(8);
  });
});

describe("getExplicacaoScoreLlmHistorico", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({
          items: [
            {
              text: "Antiga",
              provider: "fake",
              model: "m",
              policy_version: "v1",
              input_tokens: 1,
              output_tokens: 2,
              estimated_cost_usd: 0,
              latency_ms: 10,
              blocked_by_guardrail: false,
              guardrail_reason: null,
              guardrail_status: "ok",
              gerado_em: "2026-05-14T12:00:00+00:00",
              trace_id: "t0",
            },
          ],
        }),
      }),
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.clearAllMocks();
  });

  it("envia GET no path de histórico com limit na query", async () => {
    const id = "550e8400-e29b-41d4-a716-446655440000";
    const items = await getExplicacaoScoreLlmHistorico(id, 10);
    expect(items).toHaveLength(1);
    expect(fetch).toHaveBeenCalledWith(
      `http://api.test/diagnosticos/${id}/explicacao-score-llm/historico?limit=10`,
      expect.objectContaining({
        method: "GET",
        headers: expect.objectContaining({ Authorization: "Bearer tok" }),
      }),
    );
  });
});
