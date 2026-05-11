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
  const base = baseUrl.replace(/\/$/, "");
  const ehProxySameOrigin = base === "/api-backend" || base.startsWith("/api-backend");
  /** URL absoluta para teste `curl` quando o cliente aponta direto à FastAPI. */
  const healthAbsoluto =
    base.startsWith("http://") || base.startsWith("https://") ? `${base}/health` : "http://127.0.0.1:60000/health";

  if (ehProxySameOrigin) {
    return (
      `Não houve resposta ao proxy «${base}» (Next → FastAPI). ` +
      `Isto significa que o **browser não recebeu uma resposta HTTP completa** para esse URL ` +
      `(não confundir com 401/403/502 com corpo JSON — aí o problema já vem da API ou do proxy com texto legível). ` +
      `**Causas frequentes:** (A) processo Next ou API em baixo / porta errada; ` +
      `(B) pedido interrompido (mudança de página, **AbortError**, extensão); ` +
      `(C) falha de rede até ao próprio Next. ` +
      `**Mitigação já no código:** o proxy segue redirecionamentos da FastAPI **no servidor**, para não expor ao browser ` +
      `URLs com hostname interno (\`http://api:8000/...\`), que costumam aparecer como «Failed to fetch». ` +
      `**Checklist:** (1) API no ar: \`docker compose ps\` (\`api\` healthy) e \`curl -sS ${healthAbsoluto}\`. ` +
      `(2) **API_PROXY_TARGET** no processo Next: host \`npm run dev\` → \`.env.local\` com \`API_PROXY_TARGET=http://127.0.0.1:60000\`; ` +
      `Compose \`web\` → \`http://api:8000\`; reiniciar Next após mudar env. ` +
      `(3) \`NEXT_PUBLIC_API_URL=/api-backend\`. ` +
      `(4) \`docker logs qdi-web\` (procurar \`qdi_api_proxy_upstream_falhou\`) e \`docker logs qdi-api\`. ` +
      `(5) DevTools → Rede: linha do pedido — se existir **código HTTP**, copie o corpo; se aparecer **(failed)** ou **NS_ERROR**, é rede/TLS/host.`
    );
  }

  return (
    `Não houve resposta da API em «${baseUrl}». ` +
    `**Não depende de firewall:** em dev costuma ser **API parada**, **porta não escuta**, **HTTPS no front** a chamar **HTTP** na API (browser bloqueia conteúdo misto), ou **CORS**. ` +
    `Verifique: (1) no terminal \`curl -sS ${healthAbsoluto}\` — se falhar, suba o stack (\`make dev\`) e espere \`healthy\`; ` +
    `(2) URL no browser — no Compose prefira \`NEXT_PUBLIC_API_URL=/api-backend\` (não use \`http://api:8000\` no cliente); ` +
    `(3) **CORS**: origem do Next (ex. \`http://127.0.0.1:60001\`) em \`CORS_ALLOWED_ORIGINS\` na API; ` +
    `(4) abra o front em **http** em dev se a API for **http** (evite https://localhost com API em http://127…); ` +
    `(5) firewall/VPN se aplicável.`
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
