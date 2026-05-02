import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Diagnóstico guardado | QualiDiagIQ",
  description:
    "Resumo do diagnóstico preparado para gravação na sua conta B2B — próximo passo: entrar para score, PDF e painel consultor.",
};

export default function GravadoLocalLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return children;
}
