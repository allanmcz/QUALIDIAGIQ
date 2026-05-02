import { ImageResponse } from "next/og";

/** Dimensão recomendada para shares (Facebook/LinkedIn/X). */
export const BRAND_OG_SIZE = { width: 1200, height: 630 } as const;

export const BRAND_OG_ALT =
  "QualiDiagIQ — Diagnóstico tributário frente à Reforma do Consumo e ABNT NBR 17301";

/**
 * Cartão social com paleta Tributiq (navy + laranja), sem raster externo —
 * evita dependência de fontes/arquivos no runtime Edge do `next/og`.
 */
export function brandOpenGraphImageResponse(): ImageResponse {
  return new ImageResponse(
    (
      <div
        style={{
          height: "100%",
          width: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          backgroundColor: "#FFFFFF",
          padding: 56,
          fontFamily:
            'ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
        }}
      >
        <div
          style={{
            display: "flex",
            flexDirection: "row",
            alignItems: "baseline",
            fontSize: 82,
            fontWeight: 800,
            letterSpacing: "-0.03em",
            lineHeight: 1,
          }}
        >
          <span style={{ color: "#0D1B4B" }}>QualiDiag</span>
          <span style={{ color: "#F26E2A" }}>IQ</span>
        </div>
        <div
          style={{
            marginTop: 28,
            fontSize: 30,
            fontWeight: 500,
            color: "#374151",
            maxWidth: 920,
            lineHeight: 1.35,
          }}
        >
          Diagnóstico tributário · EC 132/2023 · LC 214/2025 · ABNT NBR 17301:2026
        </div>
        <div
          style={{
            marginTop: "auto",
            paddingTop: 32,
            display: "flex",
            alignItems: "center",
            gap: 10,
            fontSize: 22,
            color: "#6B7280",
          }}
        >
          <span style={{ fontWeight: 400 }}>by</span>
          <span
            style={{
              width: 12,
              height: 12,
              borderRadius: 9999,
              backgroundColor: "#F26E2A",
            }}
          />
          <span style={{ fontWeight: 700, color: "#0D1B4B" }}>Tributiq</span>
        </div>
      </div>
    ),
    { ...BRAND_OG_SIZE },
  );
}
