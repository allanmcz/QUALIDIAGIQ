import type { Metadata, Viewport } from "next";
import { Inter, Montserrat } from "next/font/google";
import "./globals.css";
import { Header } from "@/components/layout/Header";
import { Footer } from "@/components/layout/Footer";
import { AppProviders } from "@/components/providers/AppProviders";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const montserrat = Montserrat({
  subsets: ["latin"],
  variable: "--font-montserrat",
  display: "swap",
  weight: ["500", "600", "700", "800"],
});

/**
 * OG/Twitter: imagem 1200×630 gerada por `opengraph-image.tsx` / `twitter-image.tsx`.
 * Em produção definir NEXT_PUBLIC_SITE_URL (ex.: https://app.tributiq.com.br).
 */
const metadataBase = new URL(process.env["NEXT_PUBLIC_SITE_URL"] ?? "http://localhost:3010");

/** PWA / instalável — ADR-011 B1; theme alinhado ao manifest.json */
export const viewport: Viewport = {
  themeColor: "#0D1B4B",
  width: "device-width",
  initialScale: 1,
};

export const metadata: Metadata = {
  metadataBase,
  manifest: "/manifest.json",
  title: "QualiDiagIQ | Diagnóstico Tributário ABNT NBR 17301",
  description:
    "Descubra a maturidade tributária da sua empresa frente à Reforma do Consumo (EC 132/2023, LC 214/2025).",
  icons: {
    icon: [{ url: "/brand/QDI-NB2-icone-app.jpg", type: "image/jpeg" }],
    apple: "/brand/QDI-NB2-icone-app.jpg",
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
    <html lang="pt-BR" className={`${inter.variable} ${montserrat.variable} antialiased`}>
      <body className="min-h-screen flex flex-col font-sans">
        <AppProviders>
          <Header />
          <main className="flex-1 flex flex-col">{children}</main>
          <Footer />
        </AppProviders>
      </body>
    </html>
  );
}
