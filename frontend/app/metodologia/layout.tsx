import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Metodologia e pesos | QualiDiagIQ",
  description:
    "Critérios públicos do diagnóstico tributário: pesos por dimensão, perguntas e base legal (EC 132/2023, LC 214/2025, ABNT NBR 17301:2026). Transparência para diretoria e contabilidade.",
};

export default function MetodologiaLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return children;
}
