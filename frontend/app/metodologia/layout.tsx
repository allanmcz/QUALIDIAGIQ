import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Metodologia e pesos | QualiDiagIQ",
  description:
    "Transparência M03 — pesos macro do score geral e manifesto público por pergunta (LC 214/2025 art. 5º, ABNT NBR 17301:2026).",
};

export default function MetodologiaLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return children;
}
