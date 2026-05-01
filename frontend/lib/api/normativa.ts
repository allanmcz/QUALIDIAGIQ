import { getApiUrl } from "./config";

export type ValidarAncoraResponse = {
  valido: boolean;
  motivo_rejeicao: string | null;
};

/**
 * Protótipo Lexiq — âncora normativa no texto (endpoint público, sem JWT).
 */
export async function postValidarAncora(texto: string): Promise<ValidarAncoraResponse> {
  const base = getApiUrl().replace(/\/$/, "");
  const res = await fetch(`${base}/normativa/validar-ancora`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ texto }),
  });
  if (!res.ok) {
    throw new Error(`Erro na API: ${res.status}`);
  }
  return res.json() as Promise<ValidarAncoraResponse>;
}
