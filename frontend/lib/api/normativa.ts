import { getApiUrlForFetch } from "./config";

export type ValidarAncoraResponse = {
  valido: boolean;
  motivo_rejeicao: string | null;
};

/**
 * Protótipo Lexiq — âncora normativa no texto (endpoint público, sem JWT).
 */
export async function postValidarAncora(texto: string): Promise<ValidarAncoraResponse> {
  const base = getApiUrlForFetch().replace(/\/$/, "");
  const res = await fetch(`${base}/normativa/validar-ancora`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ texto }),
  });
  if (!res.ok) {
    throw new Error(`Não foi possível validar a referência agora (HTTP ${res.status}).`);
  }
  return res.json() as Promise<ValidarAncoraResponse>;
}
