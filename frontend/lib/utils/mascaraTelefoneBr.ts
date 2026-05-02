/**
 * Máscara de telefone brasileiro **sem DDI** (apenas DDD + número).
 * Celular: 11 dígitos → `(XX) XXXXX-XXXX`; fixo: 10 dígitos → `(XX) XXXX-XXXX`.
 */

/** Extrai até 11 dígitos (DDD + local). */
export function digitosTelefoneBR(valor: string): string {
  return valor.replace(/\D/g, "").slice(0, 11);
}

/** Aplica máscara para exibição no input. */
export function mascaraTelefoneBR(valor: string): string {
  const d = digitosTelefoneBR(valor);
  if (d.length === 0) return "";
  if (d.length <= 2) return `(${d}`;
  if (d.length <= 6) return `(${d.slice(0, 2)}) ${d.slice(2)}`;
  if (d.length <= 10) return `(${d.slice(0, 2)}) ${d.slice(2, 6)}-${d.slice(6)}`;
  return `(${d.slice(0, 2)}) ${d.slice(2, 7)}-${d.slice(7)}`;
}
