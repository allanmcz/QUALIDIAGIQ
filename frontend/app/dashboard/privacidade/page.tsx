import { Suspense } from "react";

import { DashboardPrivacidadeClient } from "./DashboardPrivacidadeClient";

export default function DashboardPrivacidadePage() {
  return (
    <Suspense
      fallback={
        <div className="container py-10 max-w-6xl">
          <p className="text-muted-foreground text-sm">Carregando painel de privacidade…</p>
        </div>
      }
    >
      <DashboardPrivacidadeClient />
    </Suspense>
  );
}
