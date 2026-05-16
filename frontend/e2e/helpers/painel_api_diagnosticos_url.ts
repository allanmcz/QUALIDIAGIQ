/**
 * Matcher para o primeiro argumento de `page.route`.
 *
 * O glob Playwright com "diagnosticos" + barra + wildcard duplo não cobre caminhos do tipo
 * `/api-backend/diagnosticos?limit=…` (segmento literal `diagnosticos` seguido de `?`,
 * sem barra antes da query). O pedido deixa de ser interceptado e segue para `API_PROXY_TARGET`
 * → resposta da API real (401 com JWT fictício) → `encerrarSessaoPainelSe401` →
 * `/login?sessao=expirada`.
 *
 * Exclui rotas do App Router (`/dashboard/diagnosticos/...`) — não são a API FastAPI.
 */
export function painelInterceptarUrlApiDiagnosticos(url: URL): boolean {
  const pathname = url.pathname.replace(/\/+$/, "") || "/";
  if (pathname.includes("/dashboard/diagnosticos")) return false;
  const partes = pathname.split("/").filter(Boolean);
  return partes.includes("diagnosticos");
}
