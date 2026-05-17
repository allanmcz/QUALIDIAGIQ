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

  it("traduz feature_disabled para mensagem acionável", () => {
    const item: ExplicacaoScoreLlmHttp = {
      ...base,
      blocked_by_guardrail: true,
      guardrail_reason: "feature_disabled",
    };
    expect(textoExibicaoExplicacao(item)).toContain("LLM_ROUTER_ENABLED");
  });

  it("avisa quando texto vazio sem guardrail", () => {
    expect(textoExibicaoExplicacao({ ...base, text: "  " })).toContain("Ollama");
  });

  it("não trata fallback de indisponibilidade como parecer", () => {
    const item: ExplicacaoScoreLlmHttp = {
      ...base,
      text:
        "Devido a indisponibilidade temporária do serviço de IA, a recomendação personalizada não pôde ser gerada no momento.",
    };
    expect(textoExibicaoExplicacao(item)).toContain("parecer válido");
  });

  it("exibe parecer longo com citação", () => {
    const parecer =
      "Na minha leitura, o score indica maturidade intermediária na transição CBS/IBS. " +
      "A dimensão fiscal merece atenção imediata. Base: EC 132/2023; LC 214/2025; ABNT NBR 17301:2026.";
    expect(textoExibicaoExplicacao({ ...base, text: parecer })).toBe(parecer);
  });
});
