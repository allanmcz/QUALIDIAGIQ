"use client";

/**
 * Limite de erro global — substitui o layout raiz; deve incluir `<html>` e `<body>`.
 */
export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html lang="pt-BR">
      <body className="flex min-h-screen flex-col items-center justify-center bg-slate-50 p-6 text-center">
        <h1 className="text-xl font-semibold text-slate-900">Erro na aplicação</h1>
        <p className="mt-2 max-w-md text-sm text-slate-600">{error.message}</p>
        <button
          type="button"
          onClick={() => reset()}
          className="mt-6 rounded-md bg-[#0D1B4B] px-4 py-2 text-sm font-medium text-white hover:opacity-90"
        >
          Tentar novamente
        </button>
      </body>
    </html>
  );
}
