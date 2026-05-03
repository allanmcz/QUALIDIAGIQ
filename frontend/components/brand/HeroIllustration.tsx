import Image from "next/image";

import { cn } from "@/lib/utils";

export type HeroIllustrationVariant = "dashboard" | "radar";

const sources: Record<HeroIllustrationVariant, string> = {
  dashboard: "/brand/QDI-KV1-hero-landing.jpg",
  radar: "/brand/QDI-KV2-hero-landing-radar.jpg",
};

export type HeroIllustrationProps = {
  /** KV1 painel ou KV2 radar (landing principal usa radar). */
  variant?: HeroIllustrationVariant;
  priority?: boolean;
  className?: string;
};

/**
 * Ilustração hero oficial (KV1/KV2) — decorativa; texto da página carrega o significado (a11y).
 */
export function HeroIllustration({
  variant = "radar",
  priority = false,
  className,
}: HeroIllustrationProps) {
  const src = sources[variant];
  const alt =
    variant === "radar"
      ? "Ilustração conceitual: radar de maturidade tributária e Reforma do Consumo"
      : "Ilustração conceitual: painel de diagnóstico tributário";

  return (
    <div
      className={cn(
        "relative w-full overflow-hidden rounded-2xl border border-border/70 bg-background shadow-md",
        "ring-1 ring-border/40",
        className,
      )}
    >
      {/* Fundo neutro + leve vignette: evita «chapa cinza» quando o JPG é claro */}
      <div
        className="pointer-events-none absolute inset-0 z-0 bg-gradient-to-br from-muted/15 via-transparent to-primary/[0.04]"
        aria-hidden
      />
      <Image
        src={src}
        alt={alt}
        width={1920}
        height={1080}
        priority={priority}
        sizes="(max-width: 768px) 100vw, 42vw"
        className="relative z-10 h-auto w-full max-h-[min(340px,48vh)] object-contain object-center sm:max-h-[min(400px,50vh)] md:max-h-[min(440px,52vh)]"
      />
    </div>
  );
}
