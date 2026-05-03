/**
 * Mensagens de erro HTTP quando o corpo pode ser JSON (FastAPI), texto simples ou HTML (proxy/502).
 */

/** Erros típicos do `fetch` no browser quando não há resposta HTTP (CORS, DNS, API caída, TLS). */
export function isLikelyNetworkFetchFailure(error: unknown): boolean {
  const msg = error instanceof Error ? error.message : String(error);
  return /failed to fetch|networkerror|load failed|network request failed/i.test(msg);
}

/**
 * Texto acionável para o utilizador quando `fetch` falha antes de HTTP (ex.: «Failed to fetch»).
 *
 * @param baseUrl — valor já resolvido de `getApiUrlForFetch()` (sem barra final), para mostrar no UI.
 */
export function mensagemConectividadeApiParaUsuario(baseUrl: string): string {
  return (
    `Não houve resposta da API em «${baseUrl}». Verifique: (1) serviço da API no ar ` +
    `(\`docker compose ps\`, GET \`/health\`); (2) URL acessível **no browser** — no Compose use ` +
    `NEXT_PUBLIC_API_URL=/api-backend (não use http://api:8000 no .env do Next); ` +
    `(3) CORS: o URL do front (origem) deve constar em CORS_ALLOWED_ORIGINS na API; ` +
    `(4) firewall/VPN.`
  );
}

function detalheFastApi(detail: unknown): string | null {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    const partes = detail.map((item) => {
      if (item && typeof item === "object" && "msg" in item) {
        return String((item as { msg: unknown }).msg);
      }
      return JSON.stringify(item);
    });
    return partes.join("; ");
  }
  return null;
}

/**
 * Converte corpo bruto da resposta numa mensagem legível para o utilizador.
 */
export function mensagemErroHttp(status: number, corpoTexto: string): string {
  const trimmed = corpoTexto.trim();
  if (!trimmed) {
    return `Falha na comunicação com o servidor (HTTP ${status}).`;
  }
  try {
    const j = JSON.parse(trimmed) as { detail?: unknown };
    const d = detalheFastApi(j.detail);
    if (d) return d;
  } catch {
    /* corpo não é JSON */
  }
  if (trimmed.startsWith("<")) {
    return (
      `O servidor devolveu HTML em vez de JSON (HTTP ${status}). ` +
      "Confira NEXT_PUBLIC_API_URL / proxy e se a API FastAPI está no ar."
    );
  }
  if (/internal server error/i.test(trimmed.slice(0, 80))) {
    return (
      `Erro interno no servidor (HTTP ${status}). Verifique os logs da API, variáveis Supabase e JWT.`
    );
  }
  return trimmed.length > 400 ? `${trimmed.slice(0, 400)}…` : trimmed;
}
