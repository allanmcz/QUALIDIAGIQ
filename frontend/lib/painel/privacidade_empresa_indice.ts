import type { DiagnosticoResumoApi } from "@/lib/api/lista_diagnosticos";
import {
  DIAGNOSTICOS_RESUMO_PAGE_SIZE_MAX,
  fetchDiagnosticosResumo,
} from "@/lib/api/lista_diagnosticos";

/** Empresa distinta derivada dos diagnósticos do tenant (CNPJ obrigatório). */
export type EmpresaPrivacidadeIndice = {
  cnpj14: string;
  razao_social: string;
};

const MAX_PAGINAS_INDICE = 25;

/** Carrega diagnósticos do tenant para montar índice de empresas (busca local). */
export async function carregarDiagnosticosParaIndiceEmpresas(): Promise<DiagnosticoResumoApi[]> {
  const page = DIAGNOSTICOS_RESUMO_PAGE_SIZE_MAX;
  const out: DiagnosticoResumoApi[] = [];
  for (let p = 0; p < MAX_PAGINAS_INDICE; p++) {
    const batch = await fetchDiagnosticosResumo(page, p * page);
    if (batch.length === 0) break;
    out.push(...batch);
    if (batch.length < page) break;
  }
  return out;
}

/** Agrupa por CNPJ 14 — mantém a razão social mais recente da lista (última ocorrência). */
export function agruparEmpresasDeDiagnosticos(
  lista: DiagnosticoResumoApi[],
): EmpresaPrivacidadeIndice[] {
  const map = new Map<string, EmpresaPrivacidadeIndice>();
  for (const d of lista) {
    const cnpj14 = (d.empresa_cnpj ?? "").replace(/\D/g, "").trim();
    if (cnpj14.length !== 14) continue;
    map.set(cnpj14, {
      cnpj14,
      razao_social: (d.empresa_razao_social ?? "").trim() || "—",
    });
  }
  return [...map.values()].sort((a, b) =>
    a.razao_social.localeCompare(b.razao_social, "pt-BR", { sensitivity: "base" }),
  );
}

/** Filtra empresas por trecho de CNPJ (dígitos) ou razão social. */
export function filtrarEmpresasIndice(
  empresas: EmpresaPrivacidadeIndice[],
  consulta: string,
  limite = 20,
): EmpresaPrivacidadeIndice[] {
  const t = consulta.trim().toLowerCase();
  const dig = consulta.replace(/\D/g, "");
  if (!t && dig.length < 3) return [];
  const filtradas = empresas.filter((e) => {
    if (dig.length >= 3 && e.cnpj14.includes(dig)) return true;
    if (t.length >= 2 && e.razao_social.toLowerCase().includes(t)) return true;
    return false;
  });
  return filtradas.slice(0, limite);
}
