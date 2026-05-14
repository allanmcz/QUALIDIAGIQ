"use client";

import { useEffect, useState } from "react";
import { WifiOff } from "lucide-react";

/**
 * Aviso quando o browser perde rede — Onda 4 (PWA / MANUS).
 * Não bloqueia o wizard; apenas informa que gravação e CNPJ dependem da API.
 */
export function WizardOfflineBanner() {
  const [offline, setOffline] = useState(
    typeof navigator !== "undefined" ? !navigator.onLine : false,
  );

  useEffect(() => {
    /** Sempre alinhar a `navigator.onLine` — o CDP do Playwright por vezes actualiza o estado sem disparar o par de eventos esperado. */
    const sync = () => {
      setOffline(typeof navigator !== "undefined" && !navigator.onLine);
    };
    sync();
    window.addEventListener("offline", sync);
    window.addEventListener("online", sync);
    return () => {
      window.removeEventListener("offline", sync);
      window.removeEventListener("online", sync);
    };
  }, []);

  if (!offline) return null;

  return (
    <div
      role="status"
      className="flex items-start gap-2 rounded-lg border border-amber-500/40 bg-amber-50 px-3 py-2 text-sm text-amber-950 shadow-sm dark:border-amber-500/30 dark:bg-amber-950/40 dark:text-amber-50"
    >
      <WifiOff className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
      <p className="min-w-0 leading-snug">
        Sem ligação à Internet. Podes continuar a ler o formulário, mas{" "}
        <strong>consulta CNPJ</strong>, <strong>gravação na API</strong> e{" "}
        <strong>envio de códigos</strong> só funcionam quando voltares a estar online.
      </p>
    </div>
  );
}
