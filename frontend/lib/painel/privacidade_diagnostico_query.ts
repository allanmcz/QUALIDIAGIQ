/** Query string do painel `/dashboard/privacidade` — diagnóstico em foco e secção. */

export const PRIVACIDADE_QUERY_DIAGNOSTICO_ID = "diagnostico_id";
export const PRIVACIDADE_QUERY_SECAO = "secao";

export type SecaoPrivacidadePainel = "lgpd" | "retificacoes";

export function hrefPrivacidadePainel(opts?: {
  diagnosticoId?: string;
  secao?: SecaoPrivacidadePainel;
}): string {
  const sp = new URLSearchParams();
  const id = opts?.diagnosticoId?.trim();
  if (id) sp.set(PRIVACIDADE_QUERY_DIAGNOSTICO_ID, id);
  if (opts?.secao) sp.set(PRIVACIDADE_QUERY_SECAO, opts.secao);
  const q = sp.toString();
  return `/dashboard/privacidade${q ? `?${q}` : ""}`;
}

export function parseSecaoPrivacidade(raw: string | null): SecaoPrivacidadePainel | null {
  if (raw === "lgpd" || raw === "retificacoes") return raw;
  return null;
}
