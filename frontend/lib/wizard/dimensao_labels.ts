/**
 * Rótulos PT-BR das dimensões do score (valores canónicos da API / domínio).
 */

export const ORDEM_DIMENSOES_API = [
  "fiscal",
  "estrategica",
  "contabil",
  "financeira",
  "operacional",
  "tecnologica",
  "compliance_abnt_17301",
] as const;

export const ROTULO_DIMENSAO: Record<string, string> = {
  fiscal: "Fiscal",
  estrategica: "Estratégica",
  contabil: "Contábil",
  financeira: "Financeira",
  operacional: "Operacional",
  tecnologica: "Tecnológica",
  compliance_abnt_17301: "Compliance ABNT NBR 17301",
};

export function rotuloDimensao(slug: string): string {
  return ROTULO_DIMENSAO[slug] ?? slug.replace(/_/g, " ");
}
