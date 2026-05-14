/**
 * Cookie httpOnly com o JWT do painel (BFF Next → FastAPI).
 *
 * O middleware e o proxy `/api-backend` usam este nome; manter sincronizado.
 */

/** Nome do cookie httpOnly — valor = JWT `access_token` da API. */
export const PAINEL_ACCESS_TOKEN_COOKIE = "qdi_painel_access";

/** TTL máximo do cookie (segundos) quando o JWT não traz `exp` válido. */
export const PAINEL_ACCESS_COOKIE_MAX_TTL_SEC = 86400 * 7;
