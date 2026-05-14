/**
 * Carrega metodologia e manifesto de pesos (rotas públicas de consulta do produto).
 */

import { getApiUrlForFetch } from "./config";

export type PesoMacroNormativaItemPublic = {
  peso: number;
  vigencia_inicio: string;
  vigencia_fim: string | null;
  rotulo_versao: string | null;
};

export type MetodologiaPublic = {
  versao_normativa: string;
  pesos_macro_dimensao_score_geral: Record<string, number>;
  pesos_macro_dimensao_normativa: Record<string, PesoMacroNormativaItemPublic>;
  nota_metodologica: string;
  recomendacoes_gaps_criticos: string[];
};

export type NormativaPesoPerguntaOverlayPublic = {
  peso_catalogo_json: number;
  peso_normativo_db: number;
  vigencia_inicio: string;
  vigencia_fim: string | null;
  rotulo_versao: string | null;
};

export type ManifestoPesoPerguntaPublic = {
  codigo: string;
  dimensao: string;
  tipo: string;
  peso: number;
  base_legal: string | null;
  pilar_abnt?: string | null;
  normativa_overlay?: NormativaPesoPerguntaOverlayPublic | null;
};

export type ManifestoPesosPublic = {
  versao_manifesto: string;
  versao_catalogo: string;
  formula_score_geral: string;
  nota_calibracao_m02: string;
  pesos_macro_dimensao: Record<string, number>;
  pesos_macro_dimensao_normativa: Record<string, PesoMacroNormativaItemPublic>;
  perguntas: ManifestoPesoPerguntaPublic[];
};

async function parseJson<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = `Erro ${res.status}`;
    try {
      const body: unknown = await res.json();
      if (body && typeof body === "object" && "detail" in body) {
        const d = (body as { detail: unknown }).detail;
        detail = typeof d === "string" ? d : JSON.stringify(d);
      }
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

export async function fetchMetodologiaPublic(): Promise<MetodologiaPublic> {
  const base = getApiUrlForFetch().replace(/\/$/, "");
  const res = await fetch(`${base}/diagnosticos/metodologia`, {
    headers: { Accept: "application/json" },
  });
  return parseJson<MetodologiaPublic>(res);
}

export async function fetchManifestoPesosPublic(): Promise<ManifestoPesosPublic> {
  const base = getApiUrlForFetch().replace(/\/$/, "");
  const res = await fetch(`${base}/diagnosticos/manifesto-pesos`, {
    headers: { Accept: "application/json" },
  });
  return parseJson<ManifestoPesosPublic>(res);
}
