import type { DiagnosticoResumoApi } from "@/lib/api/lista_diagnosticos";

/** Diagnóstico baseline da empresa no tenant (ciclo mais antigo — ancoragem técnica do quadro único por CNPJ). */
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

/** Quadro de implantação: um por empresa; edição só quando este id é o baseline canónico e está finalizado. */
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
