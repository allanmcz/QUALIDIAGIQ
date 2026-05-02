import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Como funciona o diagnóstico | QualiDiagIQ",
  description:
    "Entenda de forma clara como avaliamos a maturidade tributária da sua empresa frente à Reforma do Consumo e à ABNT NBR 17301:2026 — critérios transparentes e auditáveis.",
};

export default function MetodologiaLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return children;
}
