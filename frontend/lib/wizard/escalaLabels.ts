/**
 * Rótulos para perguntas `escala_1_5` — maturidade / prática organizacional (ABNT NBR 17301, etc.).
 * Catálogo pode sobrescrever via `rotulos_escala` (5 strings na API).
 */

/** Valores 1 … 5: menor número = menor maturidade / prática inexistente. */
export const ROTULOS_ESCALA_MATURIDADE_PADRAO: readonly [
  string,
  string,
  string,
  string,
  string,
] = [
  "Inexistente — não há prática reconhecível",
  "Incipiente — pontual, sem formalização",
  "Parcial — existe, mas cobertura ou evidências incompletas",
  "Estruturado — formalizado, recorrente e conhecido pela equipe",
  "Maduro — evidências, monitoramento e melhoria contínua",
];

export type CincoRotulos = readonly [string, string, string, string, string];

/** Resolve rótulos da pergunta ou cai no padrão editorial QDI. */
export function rotulosEscalaParaPergunta(rotulosDoCatalogo: string[] | null | undefined): CincoRotulos {
  if (
    Array.isArray(rotulosDoCatalogo) &&
    rotulosDoCatalogo.length === 5 &&
    rotulosDoCatalogo.every((s) => typeof s === "string" && s.trim().length > 0)
  ) {
    return rotulosDoCatalogo.map((s) => s.trim()) as unknown as CincoRotulos;
  }
  return ROTULOS_ESCALA_MATURIDADE_PADRAO;
}
