import { cn } from "@/lib/utils";

export type PoweredByBrainProps = {
  className?: string;
};

/**
 * Selo opcional para fluxos com IA (Lexiq / motor analítico) — texto discreto.
 */
export function PoweredByBrain({ className }: PoweredByBrainProps) {
  return (
    <p className={cn("text-xs text-muted-foreground", className)}>
      <span className="font-medium text-brand-navy">Powered by Tributiq Brain</span>
      <span> — inteligência normativa versionada (contexto Lexiq).</span>
    </p>
  );
}
