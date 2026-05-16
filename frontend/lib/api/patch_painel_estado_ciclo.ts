/**
 * PATCH /diagnosticos/{id}/painel-estado-ciclo — mutação com If-Match na versão otimista.
 */

import { cabecalhosAuthPainelOpcional, getApiUrlForFetch } from "@/lib/api/config";
import type { PainelEstadoCicloApi } from "@/lib/painel/painel_estado_ciclo_labels";
import type { DiagnosticoDetalheApi } from "@/types/diagnostico_detalhe";

export async function patchPainelEstadoCicloDiagnostico(args: {
  diagnosticoId: string;
  painel_estado_ciclo: PainelEstadoCicloApi;
  versao_esperada: number;
}): Promise<DiagnosticoDetalheApi> {
  const base = getApiUrlForFetch().replace(/\/$/, "");
  const res = await fetch(`${base}/diagnosticos/${args.diagnosticoId}/painel-estado-ciclo`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
      ...cabecalhosAuthPainelOpcional(),
      "If-Match": String(args.versao_esperada),
    },
    credentials: "include",
    cache: "no-store",
    body: JSON.stringify({ painel_estado_ciclo: args.painel_estado_ciclo }),
  });
  if (!res.ok) {
    const t = await res.text();
    throw new Error(`${res.status}: ${t.slice(0, 400)}`);
  }
  return (await res.json()) as DiagnosticoDetalheApi;
}
