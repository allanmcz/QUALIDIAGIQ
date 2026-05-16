/** Estados operacionais persistentes (`painel_estado_ciclo` na API) — rótulos só para UI. */

export const PAINEL_ESTADO_CICLO_VALORES = [
  "realizado",
  "em_andamento",
  "descartado",
  "finalizado",
] as const;

export type PainelEstadoCicloApi = (typeof PAINEL_ESTADO_CICLO_VALORES)[number];

export function rotuloPainelEstadoCiclo(valor: string | null | undefined): string {
  switch ((valor || "").trim()) {
    case "realizado":
      return "Realizado";
    case "em_andamento":
      return "Em andamento";
    case "descartado":
      return "Descartado";
    case "finalizado":
      return "Finalizado (consultoria)";
    default:
      return valor?.trim() ? valor : "—";
  }
}
