/**
 * Cookie não-httpOnly espelhando sessão do painel — permite ao middleware Edge (`middleware.ts`)
 * redirecionar visitas frias a `/dashboard/*` sem JWT em `localStorage` antes da hidratação.
 *
 * O JWT continua em `localStorage` (MVP); este cookie só transporta o «presente/ausente» (valor `1`).
 */

/** Nome do cookie — manter alinhado com `frontend/middleware.ts`. */
export const ADMIN_SESSION_COOKIE_FLAG = "qdi_admin_session";

const MAX_AGE_SEC = 86400 * 7;

/** Define ou remove o cookie de presença da sessão painel (LGPD: não gravar PII no cookie). */
export function setPainelSessionCookiePresent(active: boolean): void {
  if (typeof document === "undefined") return;
  if (!active) {
    document.cookie = `${ADMIN_SESSION_COOKIE_FLAG}=; path=/; max-age=0; SameSite=Lax`;
    return;
  }
  document.cookie = `${ADMIN_SESSION_COOKIE_FLAG}=1; path=/; max-age=${MAX_AGE_SEC}; SameSite=Lax`;
}
