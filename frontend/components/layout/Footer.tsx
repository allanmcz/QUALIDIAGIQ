import Link from "next/link";

import { EndorsedBadge } from "@/components/brand/EndorsedBadge";
import { Wordmark } from "@/components/brand/Wordmark";

export function Footer() {
  const ano = new Date().getFullYear();
  return (
    <footer className="border-t py-3 text-left hyphens-none md:py-0">
      <div className="container flex min-h-14 flex-nowrap items-center justify-between gap-3 overflow-x-auto py-3 md:min-h-16 md:gap-4 md:py-4">
        <div className="flex min-w-0 flex-nowrap items-center gap-2 sm:gap-3 md:gap-4">
          <Wordmark size="sm" className="shrink-0" />
          <EndorsedBadge className="shrink-0" />
          <p className="whitespace-nowrap text-xs text-muted-foreground sm:text-sm">
            &copy; {ano} QualiDiagIQ · produto Tributiq. Todos os direitos reservados.
          </p>
        </div>
        <nav
          className="flex shrink-0 flex-nowrap items-center gap-x-2 text-xs text-muted-foreground sm:gap-x-3 sm:text-sm md:gap-x-4"
          aria-label="Links institucionais"
        >
          <Link href="/metodologia" className="whitespace-nowrap hover:underline">
            Metodologia e pesos
          </Link>
          <Link href="/abnt-framework" className="whitespace-nowrap hover:underline">
            Framework ABNT
          </Link>
          <Link href="/termos" className="whitespace-nowrap hover:underline">
            Termos de Uso
          </Link>
          <Link href="/privacidade" className="whitespace-nowrap hover:underline">
            Política de Privacidade
          </Link>
          <Link href="/privacidade#dpo" className="whitespace-nowrap hover:underline">
            DPO
          </Link>
          <Link href="/avaliacao-contador" className="whitespace-nowrap hover:underline">
            Avaliação (contador)
          </Link>
        </nav>
      </div>
    </footer>
  );
}
