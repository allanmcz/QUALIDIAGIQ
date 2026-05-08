/**
 * Encarregado de Proteção de Dados (DPO) — dados públicos injetados no build do Next (`NEXT_PUBLIC_*`).
 * Em produção, definir no painel do host (Vercel, etc.) o mesmo e-mail acordado com o escritório / ANPD.
 */

export type DpoPublicContact = {
  email: string;
  /** Nome para exibição (opcional). */
  nomeExibicao?: string;
};

export function getDpoPublicContact(): DpoPublicContact | null {
  const email = process.env.NEXT_PUBLIC_LGPD_DPO_EMAIL?.trim();
  if (!email) return null;
  const nome = process.env.NEXT_PUBLIC_LGPD_DPO_NOME?.trim();
  return { email, nomeExibicao: nome || undefined };
}

/** Versão e vigência da política (opcional — transparência no cabeçalho da página). */
export function getPoliticaPublicMeta(): { versao: string; vigenciaIso: string } | null {
  const versao = process.env.NEXT_PUBLIC_POLITICA_PRIVACIDADE_VERSAO?.trim();
  const vigencia = process.env.NEXT_PUBLIC_POLITICA_PRIVACIDADE_VIGENCIA?.trim();
  if (!versao && !vigencia) return null;
  return {
    versao: versao || "—",
    vigenciaIso: vigencia || "—",
  };
}
