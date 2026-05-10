/**
 * Página de fallback offline (Workbox / ADR-011 B2).
 *
 * Referência: `.github/adr/ADR-011-pwa-next14-qualidiagiq.md`
 */
export default function OfflinePage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-4 bg-slate-950 px-6 text-center text-slate-100">
      <h1 className="text-xl font-semibold">Sem ligação à rede</h1>
      <p className="max-w-md text-sm text-slate-300">
        Verifique a sua ligação à Internet e tente novamente. O diagnóstico e o
        painel requerem ligação ao servidor.
      </p>
    </main>
  );
}
