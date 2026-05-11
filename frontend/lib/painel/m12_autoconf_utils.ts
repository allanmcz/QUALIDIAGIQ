/** Autoconf ABNT M12 — 10 controlos Likert (espelho API / JSONB). */

export const M12_NUM_ITENS = 10;

export function normalizarM12DoApi(raw: (number | boolean)[] | null): number[] | null {
  if (!Array.isArray(raw) || raw.length !== M12_NUM_ITENS) return null;
  const out: number[] = [];
  for (const x of raw) {
    if (typeof x === "boolean") out.push(x ? 5 : 1);
    else if (typeof x === "number" && Number.isInteger(x) && x >= 1 && x <= 5) out.push(x);
    else return null;
  }
  return out;
}

export function m12EstadoInicialVazio(): (number | null)[] {
  return Array.from({ length: M12_NUM_ITENS }, () => null);
}

export function m12ValoresSeCompleto(vals: (number | null)[]): number[] | null {
  if (!Array.isArray(vals) || vals.length !== M12_NUM_ITENS) return null;
  const out: number[] = [];
  for (const x of vals) {
    if (x === null || typeof x !== "number" || !Number.isInteger(x) || x < 1 || x > 5) {
      return null;
    }
    out.push(x);
  }
  return out;
}

export function rotuloLikertM12(v: number): string {
  const m: Record<number, string> = {
    1: "Não implementado",
    2: "Inicial / informal",
    3: "Parcial",
    4: "Implementado (lacunas menores)",
    5: "Implementado e monitorado",
  };
  return m[v] ?? "—";
}
