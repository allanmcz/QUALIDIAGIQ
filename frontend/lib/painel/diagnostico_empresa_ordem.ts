import type { DiagnosticoResumoApi } from "@/lib/api/lista_diagnosticos";
import { linhasQuadroGrid } from "@/lib/painel/quadro_implantacao_utils";
import type { DiagnosticoDetalheApi } from "@/types/diagnostico_detalhe";

function ordenarPorCicloAsc(rows: DiagnosticoResumoApi[]): DiagnosticoResumoApi[] {
  return [...rows].sort((a, b) => {
    const da = new Date(a.finalizado_em ?? a.criado_em).getTime();
    const db = new Date(b.finalizado_em ?? b.criado_em).getTime();
    if (da !== db) return da - db;
    return a.id.localeCompare(b.id);
  });
}

/** Diagnóstico baseline da empresa no tenant (ciclo mais antigo — ancoragem técnica do quadro único por CNPJ). */
export function idDiagnosticoMaisAntigoEmpresa(rows: DiagnosticoResumoApi[]): string | null {
  if (!rows.length) return null;
  return ordenarPorCicloAsc(rows)[0]?.id ?? null;
}

/** Baseline canónico do quadro: ciclo finalizado mais antigo; senão o mais antigo da lista. */
export function idDiagnosticoBaselineQuadroEmpresa(rows: DiagnosticoResumoApi[]): string | null {
  if (!rows.length) return null;
  const finalizados = rows.filter((r) => r.status === "finalizado");
  if (finalizados.length) return idDiagnosticoMaisAntigoEmpresa(finalizados);
  return idDiagnosticoMaisAntigoEmpresa(rows);
}

/**
 * Detalhe para a grelha no topo da empresa — prefere baseline com checklist materializado.
 */
export function escolherDetalheQuadroEmpresa(
  rows: DiagnosticoResumoApi[],
  detalhes: Record<string, DiagnosticoDetalheApi | undefined>,
): DiagnosticoDetalheApi | null {
  if (!rows.length) return null;

  const baselineId = idDiagnosticoBaselineQuadroEmpresa(rows);
  const baseline = baselineId ? detalhes[baselineId] : undefined;
  if (baseline && linhasQuadroGrid(baseline.checklist).length > 0) return baseline;

  const candidatos = ordenarPorCicloAsc(rows.filter((r) => r.status === "finalizado"));
  for (const row of candidatos) {
    const d = detalhes[row.id];
    if (d && linhasQuadroGrid(d.checklist).length > 0) return d;
  }

  return baseline ?? null;
}

/** Quadro de implantação: um por empresa; edição só quando este id é o baseline canónico e está finalizado. */
export function quadroImplantacaoEditavel(
  diagnosticoId: string,
  resumosEmpresa: DiagnosticoResumoApi[],
  status: string,
): boolean {
  if (status !== "finalizado") return false;
  const baselineId = idDiagnosticoBaselineQuadroEmpresa(resumosEmpresa);
  if (!baselineId) return true;
  return diagnosticoId === baselineId;
}
