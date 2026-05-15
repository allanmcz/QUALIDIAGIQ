import { describe, expect, it } from "vitest";

import type { ExplicacaoScoreLlmHttp } from "./explicacao_score_llm";
import {
  historicoAnterioresAExibicao,
  textoExibicaoExplicacao,
} from "./explicacao_score_llm_historico";

const base: ExplicacaoScoreLlmHttp = {
  text: "Texto A",
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
  gerado_em: "2026-05-15T12:00:00+00:00",
  trace_id: "t1",
};

describe("historicoAnterioresAExibicao", () => {
  it("remove o primeiro item quando duplica a última geração exibida", () => {
    const atual = { ...base };
    const items = [atual, { ...base, text: "Texto B", gerado_em: "2026-05-14T12:00:00+00:00" }];
    expect(historicoAnterioresAExibicao(items, atual)).toHaveLength(1);
    expect(historicoAnterioresAExibicao(items, atual)[0]?.text).toBe("Texto B");
  });

  it("devolve todos os itens quando não há geração atual", () => {
    const items = [base];
    expect(historicoAnterioresAExibicao(items, null)).toEqual(items);
  });
});

describe("textoExibicaoExplicacao", () => {
  it("prioriza guardrail_reason quando bloqueado", () => {
    const item: ExplicacaoScoreLlmHttp = {
      ...base,
      text: "ignorado",
      blocked_by_guardrail: true,
      guardrail_reason: "Sem citação Lexiq.",
    };
    expect(textoExibicaoExplicacao(item)).toBe("Sem citação Lexiq.");
  });
});
