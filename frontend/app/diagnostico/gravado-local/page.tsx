"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

/**
 * URL legada: o fluxo passou a usar `/diagnostico/confirmar-gravacao` com fragmento `#token`.
 * Mantemos redirecionamento para não quebrar links e favoritos.
 */
export default function DiagnosticoGravadoLocalRedirectPage() {
  const router = useRouter();

  useEffect(() => {
    const h = typeof window !== "undefined" ? window.location.hash : "";
    router.replace(`/diagnostico/confirmar-gravacao${h}`);
  }, [router]);

  return (
    <div className="container max-w-lg py-16 text-center text-sm text-muted-foreground">
      A redirecionar para confirmação…
    </div>
  );
}
