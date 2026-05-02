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
        "relative w-full overflow-hidden rounded-xl border border-border shadow-card",
        className,
      )}
    >
      <Image
        src={src}
        alt={alt}
        width={1920}
        height={1080}
        priority={priority}
        sizes="(max-width: 768px) 100vw, 42vw"
        className="h-auto w-full max-h-[min(380px,52vh)] object-cover object-center md:max-h-[460px]"
      />
    </div>
  );
}
