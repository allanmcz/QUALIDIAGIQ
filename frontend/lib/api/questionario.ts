import type { EmpresaData } from "../schemas/wizard";
import { getApiUrl } from "./config";

export type PerguntaCatalogo = {
  id: string;
  codigo: string;
  texto: string;
  tipo: string;
  peso: number;
  dimensao: string;
  base_legal: string | null;
};

export type QuestionarioDisponivel = {
  versao_catalogo: string;
  total: number;
  perguntas: PerguntaCatalogo[];
};

/** Monta query string alinhada ao GET `/diagnosticos/questionario` (endpoint público). */
export function buildQuestionarioSearchParams(empresa: EmpresaData): URLSearchParams {
  const p = new URLSearchParams();
  p.set("cnpj", empresa.cnpj.replace(/\D/g, ""));
  p.set("razao_social", empresa.razao_social.trim());
  p.set("porte", empresa.porte);
  p.set("regime", empresa.regime);
  p.set("cnae_principal", empresa.cnae_principal);
  p.set("uf", empresa.uf.toUpperCase());
  p.set("setor_macro", empresa.setor_macro);
  return p;
}

export async function fetchQuestionarioAdaptativo(
  empresa: EmpresaData
): Promise<QuestionarioDisponivel> {
  const base = getApiUrl().replace(/\/$/, "");
  const qs = buildQuestionarioSearchParams(empresa).toString();
  const res = await fetch(`${base}/diagnosticos/questionario?${qs}`, {
    method: "GET",
    headers: { Accept: "application/json" },
  });
  if (!res.ok) {
    let detail = `Erro ${res.status}`;
    try {
      const body = await res.json();
      if (body.detail) detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return res.json();
}
