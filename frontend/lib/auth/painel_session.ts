/**
 * Sessão do painel (conta na plataforma) — limpeza e redirecionamento em 401.
 *
 * Quando o Bearer em `localStorage` expira ou deixa de bater com `JWT_SECRET` da API
 * (ex.: rebuild do backend), o servidor responde 401 com detail «Token inválido ou expirado».
 * Neste caso limpamos o armazenamento e enviamos o utilizador ao login em vez de mostrar erro cru.
 */

import {
  clearPainelSessionStorageOnly,
} from "@/lib/api/config";

import { QDI_AUTH_CHANGED_EVENT } from "./auth_events";
import { setPainelSessionCookiePresent } from "./session_cookie";

/** Remove JWT e metadados do painel e notifica ouvintes (ex.: cabeçalho público). */
export function clearPainelSessionLocal(): void {
  if (typeof window === "undefined") return;
  clearPainelSessionStorageOnly();
  setPainelSessionCookiePresent(false);
  window.dispatchEvent(new Event(QDI_AUTH_CHANGED_EVENT));
}

/**
 * Se HTTP 401: limpa sessão do painel e navega para `/login?sessao=expirada`.
 *
 * Returns:
 *   `true` se tratou 401 (o caller deve parar — ex.: não atualizar estado de erro).
 */
export function encerrarSessaoPainelSe401(status: number): boolean {
  if (status !== 401 || typeof window === "undefined") return false;
  clearPainelSessionLocal();
  window.location.assign("/login?sessao=expirada");
  return true;
}
