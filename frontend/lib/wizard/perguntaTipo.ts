/**
 * Normalização de tipos de pergunta devolvidos pela API do questionário adaptativo.
 *
 * Camada: lib (puro — sem React)
 */

/** API pode devolver tipo com variações — unifica para o wizard não cair no ramo errado (ex.: ternária). */
export function normalizarTipoPerguntaWizard(tipo: string | undefined): string {
  return (tipo ?? "").trim().toLowerCase();
}

export function valorInicialPorTipoPergunta(tipo: string): string | number | string[] {
  const t = normalizarTipoPerguntaWizard(tipo);
  if (t === "multipla_escolha" || t === "checklist") return [];
  return "";
}

export function tipoEhEscalaLikert15(tipo: string | undefined): boolean {
  return normalizarTipoPerguntaWizard(tipo) === "escala_1_5";
}

export function tipoEhNumericaWizard(tipo: string | undefined): boolean {
  return normalizarTipoPerguntaWizard(tipo) === "numerica";
}
