import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Diagnóstico guardado | QualiDiagIQ",
  description:
    "Resumo do diagnóstico preparado para gravação na sua conta na plataforma — próximo passo: entrar para score, PDF e painel.",
};

export default function GravadoLocalLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return children;
}
