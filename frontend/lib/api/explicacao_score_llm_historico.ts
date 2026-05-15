/**
 * Filtra entradas do histórico que duplicam a geração exibida como «última» no card.
 * A API devolve mais recente primeiro; a coluna JSONB do diagnóstico espelha a última geração.
 */
import type { ExplicacaoScoreLlmHttp } from "./explicacao_score_llm";

export function historicoAnterioresAExibicao(
  items: ExplicacaoScoreLlmHttp[],
  atual: ExplicacaoScoreLlmHttp | null,
): ExplicacaoScoreLlmHttp[] {
  if (!atual || items.length === 0) return items;
  const [primeiro, ...resto] = items;
  if (!primeiro) return items;
  const mesmoInstante =
    (primeiro.gerado_em || "").trim() === (atual.gerado_em || "").trim() &&
    (primeiro.gerado_em || "").length > 0;
  const mesmoTexto = (primeiro.text || "").trim() === (atual.text || "").trim();
  if (mesmoInstante || (mesmoTexto && primeiro.text.trim().length > 0)) {
    return resto;
  }
  return items.filter(
    (it) =>
      (it.gerado_em || "").trim() !== (atual.gerado_em || "").trim() ||
      (it.text || "").trim() !== (atual.text || "").trim(),
  );
}

export function textoExibicaoExplicacao(item: ExplicacaoScoreLlmHttp): string {
  if (item.blocked_by_guardrail && item.guardrail_reason) {
    return item.guardrail_reason;
  }
  return item.text?.trim() || "—";
}
