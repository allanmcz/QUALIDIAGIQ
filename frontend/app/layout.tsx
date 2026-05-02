import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Header } from "@/components/layout/Header";
import { Footer } from "@/components/layout/Footer";

const inter = Inter({ subsets: ["latin"] });

/**
 * OG/Twitter: imagem 1200×630 gerada por `opengraph-image.tsx` / `twitter-image.tsx`.
 * Em produção definir NEXT_PUBLIC_SITE_URL (ex.: https://app.tributiq.com.br).
 */
const metadataBase = new URL(process.env["NEXT_PUBLIC_SITE_URL"] ?? "http://localhost:3010");

export const metadata: Metadata = {
  metadataBase,
  title: "QualiDiagIQ | Diagnóstico Tributário ABNT NBR 17301",
  description:
    "Descubra a maturidade tributária da sua empresa frente à Reforma do Consumo (EC 132/2023, LC 214/2025).",
  icons: {
    icon: [{ url: "/brand/QDI-NB2-icone-app.png", type: "image/png" }],
    apple: "/brand/QDI-NB2-icone-app.png",
  },
  openGraph: {
    title: "QualiDiagIQ | Diagnóstico Tributário ABNT NBR 17301",
    description:
      "Maturidade tributária frente à Reforma do Consumo e ABNT NBR 17301:2026 — ecossistema Tributiq.",
    locale: "pt_BR",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "QualiDiagIQ | Diagnóstico Tributário",
    description: "Reforma do Consumo e compliance ABNT NBR 17301:2026.",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR" className="antialiased">
      <body className={`${inter.className} min-h-screen flex flex-col`}>
        <Header />
        <main className="flex-1 flex flex-col">{children}</main>
        <Footer />
      </body>
    </html>
  );
}
