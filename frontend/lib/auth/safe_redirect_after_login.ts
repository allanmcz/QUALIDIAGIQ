/**
 * Destino interno após login — evita open redirect (apenas paths relativos na allowlist).
 */
export function destinoSeguroAposLogin(redirect: string | null): string {
  if (!redirect || !redirect.startsWith("/") || redirect.startsWith("//")) {
    return "/dashboard";
  }
  const allowedPrefixes = ["/wizard", "/dashboard", "/sucesso"];
  const ok = allowedPrefixes.some((p) => redirect === p || redirect.startsWith(`${p}/`));
  return ok ? redirect : "/dashboard";
}
