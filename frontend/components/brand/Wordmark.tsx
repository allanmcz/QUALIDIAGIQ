import { cn } from "@/lib/utils";

const sizeClass: Record<"sm" | "md" | "lg", string> = {
  sm: "text-lg",
  md: "text-xl",
  lg: "text-2xl",
};

export type WordmarkProps = {
  size?: keyof typeof sizeClass;
  className?: string;
};

/**
 * Wordmark tipográfico: "QualiDiag" navy + "IQ" laranja (sem substituir NB3 raster no Header).
 */
export function Wordmark({ size = "md", className }: WordmarkProps) {
  return (
    <span className={cn("qdi-wordmark inline-flex items-baseline", sizeClass[size], className)}>
      <span className="qdi-prefix">QualiDiag</span>
      <span className="qdi-suffix">IQ</span>
    </span>
  );
}
