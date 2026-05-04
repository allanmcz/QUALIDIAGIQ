"use client";

import { LOGO_FULL_VB_H, LOGO_FULL_VB_W } from "@/components/brand/logo_full_viewbox";
import { cn } from "@/lib/utils";

export type QualiDiagLogoFullSvgProps = {
  width: number;
  height: number;
  className?: string;
};

/**
 * Logotipo QualiDiagIQ em SVG (vetor) — nitidez em qualquer DPR, sem caixa branca do raster.
 * Cores alinhadas a `--brand-navy` / `--brand-orange` / `--brand-gray-400` (REFORMULACAO_MARCA).
 */
export function QualiDiagLogoFullSvg({ width, height, className }: QualiDiagLogoFullSvgProps) {
  const w = Number.isFinite(width) && width > 0 ? width : Math.round((68 * LOGO_FULL_VB_W) / LOGO_FULL_VB_H);
  const h = Number.isFinite(height) && height > 0 ? height : 68;

  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox={`0 0 ${LOGO_FULL_VB_W} ${LOGO_FULL_VB_H}`}
      width={w}
      height={h}
      className={cn("block shrink-0 select-none", className)}
      shapeRendering="geometricPrecision"
      role="img"
      aria-label="QualiDiagIQ — diagnóstico tributário inteligente"
    >
      {/* Ícone: lupa + barras (laranja / azul institucional / laranja) */}
      <g transform="translate(4, 6)">
        <circle cx="26" cy="26" r="19" fill="none" stroke="#0d1b4b" strokeWidth="3.25" />
        <rect x="14.5" y="31" width="4.8" height="11" rx="1" fill="#f26e2a" />
        <rect x="21.2" y="25" width="4.8" height="17" rx="1" fill="#2563eb" />
        <rect x="27.9" y="28" width="4.8" height="14" rx="1" fill="#f26e2a" />
        <path
          d="M 40 40 L 56 56"
          stroke="#0d1b4b"
          strokeWidth="4.2"
          strokeLinecap="round"
        />
      </g>
      {/* Wordmark — tspans evitam sobreposição entre «QualiDiag» e «IQ». */}
      <text
        x="72"
        y="46"
        fontFamily="system-ui, -apple-system, 'Segoe UI', sans-serif"
        fontSize="24"
        fontWeight="700"
      >
        <tspan fill="#0d1b4b">QualiDiag</tspan>
        <tspan fill="#f26e2a">IQ</tspan>
      </text>
      {/* Tagline */}
      <text
        x="72"
        y="66"
        fontFamily="system-ui, -apple-system, 'Segoe UI', sans-serif"
        fontSize="8.25"
        fontWeight="600"
        fill="#9ca3af"
        letterSpacing="0.12em"
      >
        DIAGNÓSTICO TRIBUTÁRIO INTELIGENTE
      </text>
    </svg>
  );
}
