import Link from "next/link";

/**
 * 404 global — Next.js App Router convida a rotas inexistentes (slug inválido, URL antiga).
 */
export default function NotFound() {
  return (
    <div className="flex min-h-[50vh] flex-col items-center justify-center gap-4 p-8 text-center">
      <h1 className="text-2xl font-bold text-slate-900">Página não encontrada</h1>
      <p className="max-w-md text-sm text-slate-600">
        O endereço pode estar incorreto ou o conteúdo foi movido.
      </p>
      <Link href="/" className="text-sm font-medium text-[#0D1B4B] underline underline-offset-4">
        Voltar ao início
      </Link>
    </div>
  );
}
