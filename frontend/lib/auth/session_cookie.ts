/**
 * Cookie não-httpOnly espelhando sessão do painel — permite ao middleware Edge (`middleware.ts`)
 * e ao cliente (`temSessaoPainelParaApiCliente`) saber que há sessão antes de hidratar metadados.
 *
 * Com BFF (`/api/auth/login` e `/api/auth/cadastro`), o JWT fica em cookie **httpOnly** (`qdi_painel_access`);
 * este cookie continua a transportar só o «presente/ausente» (`1`), definido no browser após sucesso.
 */

/** Nome do cookie — manter alinhado com `frontend/middleware.ts` e `app/api/auth/logout/route.ts`. */
export const ADMIN_SESSION_COOKIE_FLAG = "qdi_admin_session";

const MAX_AGE_SEC = 86400 * 7;

/** `true` se o browser envia a flag de sessão painel (não-httpOnly). */
export function isPainelSessionFlagCookiePresent(): boolean {
  if (typeof document === "undefined") return false;
  const prefix = `${ADMIN_SESSION_COOKIE_FLAG}=1`;
  return document.cookie.split(";").some((part) => part.trim().startsWith(prefix));
}

/** Define ou remove o cookie de presença da sessão painel (LGPD: não gravar PII no cookie). */
export function setPainelSessionCookiePresent(active: boolean): void {
  if (typeof document === "undefined") return;
  if (!active) {
    document.cookie = `${ADMIN_SESSION_COOKIE_FLAG}=; path=/; max-age=0; SameSite=Lax`;
    return;
  }
  document.cookie = `${ADMIN_SESSION_COOKIE_FLAG}=1; path=/; max-age=${MAX_AGE_SEC}; SameSite=Lax`;
}
