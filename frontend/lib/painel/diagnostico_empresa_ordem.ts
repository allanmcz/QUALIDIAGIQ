import type { DiagnosticoResumoApi } from "@/lib/api/lista_diagnosticos";

/** Diagnóstico mais antigo da PJ no tenant (primeiro ciclo — único com quadro editável). */
export function idDiagnosticoMaisAntigoEmpresa(rows: DiagnosticoResumoApi[]): string | null {
  if (!rows.length) return null;
  const sorted = [...rows].sort((a, b) => {
    const da = new Date(a.finalizado_em ?? a.criado_em).getTime();
    const db = new Date(b.finalizado_em ?? b.criado_em).getTime();
    if (da !== db) return da - db;
    return a.id.localeCompare(b.id);
  });
  return sorted[0]?.id ?? null;
}

/** Quadro de implantação: edição só no primeiro diagnóstico finalizado da empresa. */
export function quadroImplantacaoEditavel(
  diagnosticoId: string,
  resumosEmpresa: DiagnosticoResumoApi[],
  status: string,
): boolean {
  if (status !== "finalizado") return false;
  const primeiroId = idDiagnosticoMaisAntigoEmpresa(resumosEmpresa);
  if (!primeiroId) return true;
  return diagnosticoId === primeiroId;
}
