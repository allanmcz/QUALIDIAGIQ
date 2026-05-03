/**
 * Migração única: chaves antigas em sessionStorage → localStorage, depois remove sessionStorage.
 * Política QDI: não manter dados de fluxo em sessionStorage (fonte canónica na API/PostgreSQL).
 */

export function migrarChaveDeSessionParaLocalStorage(key: string): void {
  if (typeof window === "undefined") return;
  try {
    const v = window.sessionStorage.getItem(key);
    if (v == null || v === "") return;
    if (!window.localStorage.getItem(key)) {
      window.localStorage.setItem(key, v);
    }
    window.sessionStorage.removeItem(key);
  } catch {
    /* quota / modo privado */
  }
}
