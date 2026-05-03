import Image from "next/image";

import { cn } from "@/lib/utils";

/** NB1 completo, NB5 layout alternativo, NB2 ícone, NB4 monoline, NB3 wordmark — raster JPG v2. */
export type LogoVariant = "full" | "layout-alt" | "icon" | "monoline" | "wordmark";
export type LogoSize = "sm" | "md" | "lg" | "xl" | "2xl";

const heightsPx: Record<LogoVariant, Record<LogoSize, number>> = {
  full: { sm: 32, md: 40, lg: 48, xl: 56, "2xl": 68 },
  "layout-alt": { sm: 32, md: 40, lg: 48, xl: 56, "2xl": 68 },
  icon: { sm: 24, md: 32, lg: 40, xl: 48, "2xl": 56 },
  monoline: { sm: 24, md: 32, lg: 40, xl: 48, "2xl": 56 },
  wordmark: { sm: 28, md: 34, lg: 42, xl: 52, "2xl": 60 },
};

const sources: Record<LogoVariant, string> = {
  full: "/brand/QDI-NB1-logo-completo.jpg",
  "layout-alt": "/brand/QDI-NB5-logo-layout-alt.jpg",
  icon: "/brand/QDI-NB2-icone-app.jpg",
  monoline: "/brand/QDI-NB4-glyph-monoline.jpg",
  wordmark: "/brand/QDI-NB3-wordmark.jpg",
};

/** Proporções oficiais Nano Banana v2 (1920×540, 2400×1080 wordmark, quadrados NB2/NB4). */
function logoRenderedWidth(variant: LogoVariant, heightPx: number): number {
  if (variant === "icon" || variant === "monoline") {
    return heightPx;
  }
  if (variant === "wordmark") {
    return Math.round(heightPx * (2400 / 1080));
  }
  return Math.round(heightPx * (1920 / 540));
}

function logoMaxWidthPx(variant: LogoVariant): number {
  if (variant === "icon" || variant === "monoline") {
    return 512;
  }
  if (variant === "wordmark") {
    return 360;
  }
  /** NB1 completo: largura máxima no header (size 2xl ~ 242px de largura renderizada). */
  return 420;
}

export type LogoProps = {
  variant?: LogoVariant;
  size?: LogoSize;
  className?: string;
  priority?: boolean;
};

/**
 * Logotipo QualiDiagIQ — assets JPG em `public/brand/` (REFORMULACAO_MARCA v2).
 */
export function Logo({ variant = "full", size = "md", className, priority = false }: LogoProps) {
  const h = heightsPx[variant][size];
  const src = sources[variant];
  const natural = logoRenderedWidth(variant, h);
  const maxW = logoMaxWidthPx(variant);
  const displayW = Math.min(natural, maxW);

  return (
    <span
      className={cn("relative inline-block shrink-0 overflow-hidden", className)}
      style={{ width: displayW, height: h }}
    >
      <Image
        src={src}
        alt="QualiDiagIQ"
        priority={priority}
        fill
        sizes={`${displayW}px`}
        className="object-contain object-left"
      />
    </span>
  );
}
