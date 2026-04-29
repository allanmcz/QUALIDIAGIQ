export function Footer() {
  return (
    <footer className="border-t py-6 md:py-0">
      <div className="container flex flex-col items-center justify-between gap-4 md:h-16 md:flex-row text-sm text-muted-foreground">
        <p>
          &copy; {new Date().getFullYear()} Tributiq. Todos os direitos reservados.
        </p>
        <div className="flex gap-4">
          <a href="#" className="hover:underline">Termos de Uso</a>
          <a href="#" className="hover:underline">Política de Privacidade</a>
        </div>
      </div>
    </footer>
  );
}
