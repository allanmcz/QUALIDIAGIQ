import Image from "next/image";

import { cn } from "@/lib/utils";

export type LogoVariant = "full" | "icon" | "wordmark";
export type LogoSize = "sm" | "md" | "lg" | "xl";

const heightsPx: Record<LogoVariant, Record<LogoSize, number>> = {
  full: { sm: 28, md: 34, lg: 42, xl: 52 },
  icon: { sm: 24, md: 32, lg: 40, xl: 48 },
  wordmark: { sm: 28, md: 34, lg: 42, xl: 52 },
};

const sources: Record<LogoVariant, string> = {
  full: "/brand/QDI-NB1-logo-completo.png",
  icon: "/brand/QDI-NB2-icone-app.png",
  wordmark: "/brand/QDI-NB3-wordmark.png",
};

export type LogoProps = {
  variant?: LogoVariant;
  size?: LogoSize;
  className?: string;
  priority?: boolean;
};

/**
 * Logotipo QualiDiagIQ (NB1 completo, NB2 ícone, NB3 wordmark raster).
 * Assets em `public/brand/` conforme REFORMULACAO_MARCA.
 */
export function Logo({ variant = "full", size = "md", className, priority = false }: LogoProps) {
  const h = heightsPx[variant][size];
  const src = sources[variant];
  const width = variant === "icon" ? h : Math.round(h * 3.6);

  return (
    <Image
      src={src}
      alt="QualiDiagIQ"
      width={width}
      height={h}
      priority={priority}
      className={cn("w-auto object-contain object-left", className)}
      style={{ height: h, width: "auto", maxWidth: variant === "icon" ? h : 280 }}
    />
  );
}
