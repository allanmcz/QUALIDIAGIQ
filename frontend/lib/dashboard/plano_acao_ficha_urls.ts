/**
 * Rotas da ficha unificada de ação do plano (grelha + Kanban).
 */

import { parseCnpjFromRouteSegment } from "@/lib/dashboard/empresa_diagnostico_urls";

export const QUERY_DIAGNOSTICO_ID = "diagnostico_id";
export const QUERY_RAZAO_SOCIAL = "razao_social";
/** Query ao voltar da ficha após gravar com sucesso. */
export const QUERY_FICHA_SALVA = "ficha_salva";

export type PlanoAcaoFichaHrefOpts = {
  diagnosticoId: string;
  razaoSocial?: string;
  /** Âncora ao voltar (ex.: `empresa-quadro-implantacao-principal`). */
  hashVolta?: string;
};

/** Path canónico: `/dashboard/empresas/{cnpj}/acao/{plano_acao_id}`. */
export function buildPlanoAcaoFichaHref(
  cnpj14: string,
  planoAcaoId: string,
  opts: PlanoAcaoFichaHrefOpts,
): string {
  const c = cnpj14.replace(/\D/g, "");
  const q = new URLSearchParams();
  q.set(QUERY_DIAGNOSTICO_ID, opts.diagnosticoId);
  const r = (opts.razaoSocial ?? "").trim();
  if (r.length >= 3) q.set(QUERY_RAZAO_SOCIAL, r);
  const base = `/dashboard/empresas/${c}/acao/${planoAcaoId}`;
  const path = `${base}?${q.toString()}`;
  const hash = opts.hashVolta?.replace(/^#/, "").trim();
  return hash ? `${path}#${hash}` : path;
}

export function buildVoltaEmpresaHref(
  cnpj14: string,
  razaoSocial?: string,
  hash?: string,
  opts?: { fichaSalva?: boolean },
): string {
  const c = cnpj14.replace(/\D/g, "");
  const q = new URLSearchParams();
  const r = (razaoSocial ?? "").trim();
  if (r.length >= 3) q.set("razao_social", r);
  if (opts?.fichaSalva) q.set(QUERY_FICHA_SALVA, "1");
  const qs = q.toString();
  const base = qs ? `/dashboard/empresas/${c}?${qs}` : `/dashboard/empresas/${c}`;
  const h = hash?.replace(/^#/, "").trim();
  return h ? `${base}#${h}` : base;
}

export function parsePlanoAcaoIdFromRoute(segment: string): string | null {
  const v = segment.trim();
  if (v.length >= 32 && /^[0-9a-f-]{36}$/i.test(v)) return v;
  return null;
}

export function parseFichaSearchParams(sp: URLSearchParams): {
  diagnosticoId: string | null;
  razaoSocial: string;
} {
  const did = sp.get(QUERY_DIAGNOSTICO_ID)?.trim() ?? null;
  let razao = sp.get(QUERY_RAZAO_SOCIAL)?.trim() ?? "";
  try {
    if (razao) razao = decodeURIComponent(razao);
  } catch {
    /* ignore */
  }
  return {
    diagnosticoId: did && /^[0-9a-f-]{36}$/i.test(did) ? did : null,
    razaoSocial: razao,
  };
}

export function parseCnpjParam(segment: string): string | null {
  return parseCnpjFromRouteSegment(segment);
}
