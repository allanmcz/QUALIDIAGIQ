import { getApiUrl } from "@/lib/api/config";

export type CnaeSubclasseItem = {
  subclasse_id: string;
  descricao: string;
};

export type CnaeBuscaResponse = {
  itens: CnaeSubclasseItem[];
};

/**
 * GET público — autocomplete CNAE 2.3 (backend: DATABASE_URL + migrações 0013/0014).
 * O wizard pode rodar sem login; não enviar Bearer.
 */
export async function fetchCnaeSubclasses(
  q: string,
  limite = 15,
): Promise<CnaeBuscaResponse> {
  const base = getApiUrl().replace(/\/$/, "");
  const params = new URLSearchParams({
    q: q.trim(),
    limite: String(Math.min(Math.max(limite, 1), 50)),
  });
  const res = await fetch(`${base}/referencia/cnae/subclasses?${params}`, {
    headers: { Accept: "application/json" },
    cache: "no-store",
  });
  if (res.status === 503) {
    throw new Error(
      "Sugestões de CNAE indisponíveis no momento. Informe os 7 dígitos do código manualmente ou tente de novo em instantes.",
    );
  }
  if (!res.ok) {
    const detalhe = await res.text();
    throw new Error(detalhe || `CNAE HTTP ${res.status}`);
  }
  return (await res.json()) as CnaeBuscaResponse;
}
