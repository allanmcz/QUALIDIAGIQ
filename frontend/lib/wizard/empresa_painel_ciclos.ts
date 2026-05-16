/**
 * Contagem de ciclos (diagnósticos) de uma PJ no tenant do painel — UX «novo ciclo».
 */

import {
  DIAGNOSTICOS_RESUMO_PAGE_SIZE_MAX,
  fetchDiagnosticosResumo,
  type DiagnosticoResumoApi,
} from "@/lib/api/lista_diagnosticos";

export type ResumoCiclosEmpresaPainel = {
  totalCiclos: number;
  /** Maior `numero_interno_grupo` visto + 1; fallback `totalCiclos + 1` se ausente. */
  proximoNumeroInternoEstimado: number;
  razaoSocialMaisRecente: string | null;
};

function calcularProximoNumero(rows: DiagnosticoResumoApi[]): number {
  let maxNim = 0;
  for (const r of rows) {
    const n = r.numero_interno_grupo;
    if (typeof n === "number" && n > maxNim) maxNim = n;
  }
  if (maxNim > 0) return maxNim + 1;
  return rows.length + 1;
}

/**
 * Lista diagnósticos do tenant filtrados por CNPJ (até uma página API).
 */
export async function fetchResumoCiclosEmpresaPainel(cnpj14: string): Promise<ResumoCiclosEmpresaPainel> {
  const digits = cnpj14.replace(/\D/g, "");
  if (digits.length !== 14) {
    return { totalCiclos: 0, proximoNumeroInternoEstimado: 1, razaoSocialMaisRecente: null };
  }
  const rows = await fetchDiagnosticosResumo(DIAGNOSTICOS_RESUMO_PAGE_SIZE_MAX, 0, {
    empresaCnpj14: digits,
  });
  const razao =
    rows.find((r) => r.empresa_razao_social?.trim())?.empresa_razao_social?.trim() ?? null;
  return {
    totalCiclos: rows.length,
    proximoNumeroInternoEstimado: calcularProximoNumero(rows),
    razaoSocialMaisRecente: razao,
  };
}
