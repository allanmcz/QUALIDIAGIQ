/**
 * Mensagens de erro HTTP quando o corpo pode ser JSON (FastAPI), texto simples ou HTML (proxy/502).
 */

/** Erros típicos do `fetch` no browser quando não há resposta HTTP utilizável (DNS, TCP, TLS, bloqueio). */
export function isLikelyNetworkFetchFailure(error: unknown): boolean {
  const msg = error instanceof Error ? error.message : String(error);
  const nome = error instanceof Error ? error.name : "";
  return (
    /failed to fetch|networkerror|load failed|network request failed/i.test(msg) ||
    nome === "AbortError"
  );
}

/**
 * Texto acionável para o utilizador quando `fetch` falha antes de HTTP (ex.: «Failed to fetch»).
 *
 * @param baseUrl — valor já resolvido de `getApiUrlForFetch()` (sem barra final), para mostrar no UI.
 */
export function mensagemConectividadeApiParaUsuario(baseUrl: string): string {
  void baseUrl;
  return (
    "Não foi possível conectar ao serviço do QualiDiagIQ neste momento. " +
    "Tente novamente em instantes; se o problema continuar, acione o suporte para verificar a disponibilidade do painel."
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
    return `Falha na comunicação com o serviço (HTTP ${status}).`;
  }
  try {
    const j = JSON.parse(trimmed) as { detail?: unknown };
    const d = detalheFastApi(j.detail);
    if (d) return d;
  } catch {
    /* corpo não é JSON */
  }
  if (trimmed.startsWith("<")) {
    return `Não foi possível interpretar a resposta do serviço (HTTP ${status}). Tente novamente em instantes.`;
  }
  if (/internal server error/i.test(trimmed.slice(0, 80))) {
    return `Erro interno temporário (HTTP ${status}). Tente novamente em instantes ou acione o suporte.`;
  }
  return trimmed.length > 400 ? `${trimmed.slice(0, 400)}…` : trimmed;
}
