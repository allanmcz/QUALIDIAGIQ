import { cn } from "@/lib/utils";

export type EndorsedBadgeProps = {
  className?: string;
};

/**
 * Endosso institucional: "by" + ponto laranja + "Tributiq" (marca-mãe).
 */
export function EndorsedBadge({ className }: EndorsedBadgeProps) {
  return (
    <span
      className={cn("inline-flex items-center gap-1.5 text-sm text-brand-gray-700", className)}
      aria-label="Produto da plataforma Tributiq"
    >
      <span className="font-normal">by</span>
      <span
        className="inline-block h-2 w-2 shrink-0 rounded-full bg-brand-orange"
        aria-hidden
      />
      <span className="font-bold text-brand-navy">Tributiq</span>
    </span>
  );
}
