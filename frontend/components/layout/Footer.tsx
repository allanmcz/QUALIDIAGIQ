import Link from "next/link";

import { EndorsedBadge } from "@/components/brand/EndorsedBadge";
import { Wordmark } from "@/components/brand/Wordmark";

export function Footer() {
  const ano = new Date().getFullYear();
  return (
    <footer className="border-t py-6 md:py-0">
      <div className="container flex flex-col items-center justify-between gap-6 md:h-auto md:min-h-16 md:flex-row md:gap-4 md:py-4">
        <div className="flex flex-col items-center gap-2 sm:flex-row sm:items-center sm:gap-4">
          <Wordmark size="sm" />
          <EndorsedBadge />
        </div>
        <p className="text-sm text-muted-foreground">
          &copy; {ano} QualiDiagIQ · produto Tributiq. Todos os direitos reservados.
        </p>
        <nav
          className="flex flex-wrap justify-center gap-x-4 gap-y-2 text-sm text-muted-foreground"
          aria-label="Links institucionais"
        >
          <Link href="/metodologia" className="hover:underline">
            Metodologia e pesos
          </Link>
          <Link href="/abnt-framework" className="hover:underline">
            Framework ABNT
          </Link>
          <Link href="/termos" className="hover:underline">
            Termos de Uso
          </Link>
          <Link href="/privacidade" className="hover:underline">
            Política de Privacidade
          </Link>
          <Link href="/avaliacao-contador" className="hover:underline">
            Avaliação (contador)
          </Link>
        </nav>
      </div>
    </footer>
  );
}
