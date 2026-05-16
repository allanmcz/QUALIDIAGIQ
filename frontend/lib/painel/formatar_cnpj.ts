/** Formata CNPJ 14 dígitos para exibição `00.000.000/0000-00`. */
export function mascaraCnpj14(digitos14: string): string {
  const d = digitos14.replace(/\D/g, "").slice(0, 14);
  if (d.length !== 14) return digitos14;
  return `${d.slice(0, 2)}.${d.slice(2, 5)}.${d.slice(5, 8)}/${d.slice(8, 12)}-${d.slice(12, 14)}`;
}
