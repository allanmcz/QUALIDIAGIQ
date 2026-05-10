/**
 * Suspense boundary por defeito na árvore App Router — UX consistente entre páginas.
 */
export default function RootLoading() {
  return (
    <div className="flex min-h-[40vh] items-center justify-center" aria-busy="true" aria-live="polite">
      <div
        className="h-10 w-10 animate-spin rounded-full border-2 border-slate-300 border-t-[#0D1B4B]"
        role="status"
      />
      <span className="sr-only">A carregar…</span>
    </div>
  );
}
