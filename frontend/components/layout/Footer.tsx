import Link from "next/link";

export function Footer() {
  return (
    <footer className="border-t py-6 md:py-0">
      <div className="container flex flex-col items-center justify-between gap-4 md:h-16 md:flex-row text-sm text-muted-foreground">
        <p>
          &copy; {new Date().getFullYear()} Tributiq. Todos os direitos reservados.
        </p>
        <nav className="flex flex-wrap justify-center gap-x-4 gap-y-2" aria-label="Links institucionais">
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
