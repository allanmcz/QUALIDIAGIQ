import { getAccessToken, getApiUrl } from "@/lib/api/config";

export type CnaeSubclasseItem = {
  subclasse_id: string;
  descricao: string;
};

export type CnaeBuscaResponse = {
  itens: CnaeSubclasseItem[];
};

/**
 * GET autenticado — autocomplete CNAE 2.3 (backend precisa DATABASE_URL + migrações 0013/0014).
 */
export async function fetchCnaeSubclasses(
  q: string,
  limite = 15,
): Promise<CnaeBuscaResponse> {
  const token = getAccessToken();
  if (!token) {
    throw new Error("Sessão ausente para consultar CNAE.");
  }
  const base = getApiUrl().replace(/\/$/, "");
  const params = new URLSearchParams({
    q: q.trim(),
    limite: String(Math.min(Math.max(limite, 1), 50)),
  });
  const res = await fetch(`${base}/referencia/cnae/subclasses?${params}`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  if (res.status === 503) {
    throw new Error("Serviço CNAE indisponível (DATABASE_URL ou migrações).");
  }
  if (res.status === 401) {
    throw new Error("Não autorizado — faça login novamente.");
  }
  if (!res.ok) {
    const detalhe = await res.text();
    throw new Error(detalhe || `CNAE HTTP ${res.status}`);
  }
  return (await res.json()) as CnaeBuscaResponse;
}
