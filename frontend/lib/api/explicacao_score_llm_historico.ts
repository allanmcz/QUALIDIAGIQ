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

import { parecerExplicacaoScoreSubstantivo } from "./explicacao_score_llm_parecer";

const MOTIVO_GUARDRAIL_PT: Record<string, string> = {
  feature_disabled:
    "Explicação por IA desactivada no servidor (LLM_ROUTER_ENABLED). Active o router LLM em dev ou contacte o suporte.",
  circuit_breaker_open:
    "Serviço de IA temporariamente indisponível (circuit breaker). Aguarde alguns minutos e tente novamente.",
  adapter_exception:
    "O Ollama não concluiu a geração (timeout ou erro). Verifique `make dev` e `OLLAMA_TIMEOUT_SECONDS` (≥ 120 s) e tente «Gerar novamente».",
  parecer_nao_substantivo:
    "A IA não devolveu um parecer válido sobre o score. Tente «Gerar novamente» — a 1.ª inferência pode levar até 2 minutos.",
  rag_base_insuficiente:
    "Base normativa insuficiente para explicação auditável. Execute a ingestão RAG ou ajuste o corpus antes de gerar novamente.",
};

export function textoExibicaoExplicacao(item: ExplicacaoScoreLlmHttp): string {
  if (item.blocked_by_guardrail && item.guardrail_reason) {
    const chave = item.guardrail_reason.trim();
    return MOTIVO_GUARDRAIL_PT[chave] ?? chave;
  }
  const texto = item.text?.trim();
  if (texto && parecerExplicacaoScoreSubstantivo(texto)) return texto;
  if (texto?.startsWith("Recomendação não exibida:")) {
    return texto;
  }
  if (texto) {
    return MOTIVO_GUARDRAIL_PT.parecer_nao_substantivo;
  }
  return "A IA não devolveu texto. Tente «Gerar novamente» ou verifique o Ollama no servidor.";
}

/** True quando há parecer consultivo exibível (não erro de adapter/guardrail). */
export function explicacaoScoreTemParecerExibivel(item: ExplicacaoScoreLlmHttp): boolean {
  if (item.blocked_by_guardrail) return false;
  return parecerExplicacaoScoreSubstantivo(item.text);
}
