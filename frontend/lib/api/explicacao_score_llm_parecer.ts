/**
 * Validação client-side do parecer Ollama (espelha regras do backend).
 */

export function parecerExplicacaoScoreSubstantivo(texto: string | null | undefined): boolean {
  const out = (texto ?? "").trim();
  if (out.length < 80) return false;
  if (out.startsWith("Recomendação não exibida:")) return false;
  const baixo = out.toLowerCase();
  if (baixo.includes("indisponibilidade temporária")) return false;
  if (baixo.includes("recomendação não gerada pelo modelo")) return false;
  if (baixo.includes("erro ao processar a recomendação")) return false;
  return true;
}
