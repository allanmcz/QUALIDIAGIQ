/**
 * Destino interno após login — evita open redirect (apenas paths relativos na allowlist).
 */
const PAINEL_POS_LOGIN = "/dashboard/diagnosticos";

/**
 * Após autenticação, o quadro canónico é a lista de diagnósticos (`/dashboard/diagnosticos`).
 * A vista por CNPJ (`/dashboard/empresas/...`) só serve de contexto — não reabrir diretamente após login
 * (middleware capturava esse path em `redirect`).
 */
function pathSemQuery(redirect: string): string {
  const i = redirect.indexOf("?");
  return (i === -1 ? redirect : redirect.slice(0, i)) || redirect;
}

export function destinoSeguroAposLogin(redirect: string | null): string {
  if (!redirect || !redirect.startsWith("/") || redirect.startsWith("//")) {
    return PAINEL_POS_LOGIN;
  }
  const path = pathSemQuery(redirect);
  if (path.startsWith("/dashboard/empresas/")) {
    return PAINEL_POS_LOGIN;
  }
  const allowedPrefixes = ["/wizard", "/dashboard", "/sucesso"];
  const ok = allowedPrefixes.some((p) => redirect === p || redirect.startsWith(`${p}/`));
  return ok ? redirect : PAINEL_POS_LOGIN;
}
