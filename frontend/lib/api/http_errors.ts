/**
 * Mensagens de erro HTTP quando o corpo pode ser JSON (FastAPI), texto simples ou HTML (proxy/502).
 */

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
