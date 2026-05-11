import { describe, expect, it } from "vitest";

import type { DiagnosticoDetalheApi } from "@/types/diagnostico_detalhe";

import {
  aggregateRankingGapsEmpresa,
  radarRowsFromScore,
  rankingGapsFromScore,
} from "./diagnostico_scores";

const scoreA: DiagnosticoDetalheApi["score"] = {
  score_geral: { valor: 55 },
  score_por_dimensao: {
    fiscal: { valor: 40, peso_total_aplicado: 1.5 },
    tecnologica: { valor: 60, peso_total_aplicado: 1.3 },
  },
};

const scoreB: DiagnosticoDetalheApi["score"] = {
  score_geral: { valor: 60 },
  score_por_dimensao: {
    fiscal: { valor: 60, peso_total_aplicado: 1.5 },
    tecnologica: { valor: 40, peso_total_aplicado: 1.3 },
  },
};

describe("rankingGapsFromScore", () => {
  it("ordena menor score primeiro", () => {
    const rows = rankingGapsFromScore(scoreA);
    expect(rows[0]?.dimensao).toBe("fiscal");
    expect(rows[0]?.valor).toBe(40);
    expect(rows[1]?.dimensao).toBe("tecnologica");
  });

  it("retorna vazio sem score", () => {
    expect(rankingGapsFromScore(null)).toEqual([]);
  });
});

describe("radarRowsFromScore", () => {
  it("mapeia dimensões sem ordenar", () => {
    const rows = radarRowsFromScore(scoreA);
    expect(rows).toHaveLength(2);
    expect(rows?.some((r) => r.dimensao === "fiscal" && r.valor === 40)).toBe(true);
  });

  it("null sem dimensões", () => {
    expect(radarRowsFromScore(null)).toBeNull();
  });
});

describe("aggregateRankingGapsEmpresa", () => {
  it("calcula média por dimensão e ordena pela menor média", () => {
    const agg = aggregateRankingGapsEmpresa([{ score: scoreA }, { score: scoreB }]);
    const fiscal = agg.find((r) => r.dimensao === "fiscal");
    const tech = agg.find((r) => r.dimensao === "tecnologica");
    expect(fiscal?.valor).toBe(50);
    expect(tech?.valor).toBe(50);
    expect(agg).toHaveLength(2);
    expect(agg.every((r) => r.valor === 50)).toBe(true);
  });

  it("lista vazia retorna vazio", () => {
    expect(aggregateRankingGapsEmpresa([])).toEqual([]);
  });
});
