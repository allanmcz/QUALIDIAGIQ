/**
 * Resultado mínimo do POST self-service — guardado em sessionStorage até à página de conclusão.
 */

export const STORAGE_SELF_SERVICE_DIAGNOSTICO_RESULT = "qdi_self_service_diag_result_v1";

export type SelfServiceDiagnosticoResultado = {
  id: string;
  status: string;
  empresa_razao_social: string;
  score_geral: number | null;
  locale_relatorio: string;
};

export function saveSelfServiceDiagnosticoResultado(data: SelfServiceDiagnosticoResultado): void {
  if (typeof window === "undefined") return;
  try {
    sessionStorage.setItem(STORAGE_SELF_SERVICE_DIAGNOSTICO_RESULT, JSON.stringify(data));
  } catch {
    /* quota */
  }
}

export function loadSelfServiceDiagnosticoResultado(): SelfServiceDiagnosticoResultado | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = sessionStorage.getItem(STORAGE_SELF_SERVICE_DIAGNOSTICO_RESULT);
    if (!raw) return null;
    const data: unknown = JSON.parse(raw);
    if (!data || typeof data !== "object") return null;
    const o = data as Record<string, unknown>;
    const id = o["id"];
    const status = o["status"];
    const empresa_razao_social = o["empresa_razao_social"];
    const locale_relatorio = o["locale_relatorio"];
    const score_geral = o["score_geral"];
    if (typeof id !== "string" || typeof status !== "string") return null;
    if (typeof empresa_razao_social !== "string") return null;
    if (typeof locale_relatorio !== "string") return null;
    const score =
      score_geral === null || score_geral === undefined
        ? null
        : typeof score_geral === "number"
          ? score_geral
          : Number(score_geral);
    return {
      id,
      status,
      empresa_razao_social,
      locale_relatorio,
      score_geral: Number.isFinite(score) ? score : null,
    };
  } catch {
    return null;
  }
}

export function clearSelfServiceDiagnosticoResultado(): void {
  if (typeof window === "undefined") return;
  try {
    sessionStorage.removeItem(STORAGE_SELF_SERVICE_DIAGNOSTICO_RESULT);
  } catch {
    /* ignore */
  }
}
