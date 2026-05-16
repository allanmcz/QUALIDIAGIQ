/**
 * Pré-preenche passo 2 do wizard a partir do diagnóstico mais recente da PJ no tenant.
 */

import { fetchDiagnosticoDetalhe } from "@/lib/api/fetch_diagnostico_detalhe";
import { fetchDiagnosticosResumoTodasPaginasPorEmpresa } from "@/lib/api/lista_diagnosticos";
import type { DiagnosticoPayloadFormInput } from "@/lib/schemas/wizard";
import type { DiagnosticoDetalheApi } from "@/types/diagnostico_detalhe";

const PORTES = new Set(["micro", "pequeno", "medio", "grande"]);
const REGIMES = new Set(["simples_nacional", "lucro_presumido", "lucro_real", "mei"]);
const SETORES = new Set(["comercio", "industria", "servicos", "agro", "consumo"]);

export type PerfilEmpresaWizardPrefill = Pick<
  DiagnosticoPayloadFormInput["empresa"],
  "porte" | "regime" | "cnae_principal" | "uf" | "setor_macro"
>;

function normalizarPorte(raw: string): string {
  const p = raw.trim().toLowerCase();
  if (p === "media") return "medio";
  return p;
}

/** Mapeia GET /diagnosticos/{id} → campos do passo 2 (exportado para testes unitários). */
export function mapDetalheParaPerfilEmpresa(
  d: DiagnosticoDetalheApi,
): PerfilEmpresaWizardPrefill | null {
  const porte = normalizarPorte(d.empresa_porte ?? "");
  const regime = (d.empresa_regime ?? "").trim().toLowerCase();
  const cnae = (d.empresa_cnae ?? "").replace(/\D/g, "").slice(0, 7);
  const uf = (d.empresa_uf ?? "").trim().toUpperCase();
  const setor = (d.empresa_setor_macro ?? "").trim().toLowerCase();

  const perfil: Partial<PerfilEmpresaWizardPrefill> = {};
  if (PORTES.has(porte)) perfil.porte = porte as PerfilEmpresaWizardPrefill["porte"];
  if (REGIMES.has(regime)) perfil.regime = regime as PerfilEmpresaWizardPrefill["regime"];
  if (cnae.length === 7) perfil.cnae_principal = cnae;
  if (uf.length === 2) perfil.uf = uf as PerfilEmpresaWizardPrefill["uf"];
  if (SETORES.has(setor)) perfil.setor_macro = setor as PerfilEmpresaWizardPrefill["setor_macro"];

  if (Object.keys(perfil).length === 0) return null;
  return perfil as PerfilEmpresaWizardPrefill;
}

/** Último ciclo por data (finalizado ou criado). */
export async function fetchPerfilEmpresaUltimoCicloPainel(
  cnpj14: string,
): Promise<PerfilEmpresaWizardPrefill | null> {
  const digits = cnpj14.replace(/\D/g, "");
  if (digits.length !== 14) return null;

  const rows = await fetchDiagnosticosResumoTodasPaginasPorEmpresa(digits);
  if (!rows.length) return null;

  const ordenados = [...rows].sort((a, b) => {
    const da = new Date(a.finalizado_em ?? a.criado_em).getTime();
    const db = new Date(b.finalizado_em ?? b.criado_em).getTime();
    return db - da;
  });

  /** Percorre ciclos do mais recente ao mais antigo até achar perfil materializado na API. */
  for (const row of ordenados.slice(0, 8)) {
    if (!row.id) continue;
    try {
      const detalhe = await fetchDiagnosticoDetalhe(row.id);
      const perfil = mapDetalheParaPerfilEmpresa(detalhe);
      if (perfil) return perfil;
    } catch {
      continue;
    }
  }
  return null;
}
