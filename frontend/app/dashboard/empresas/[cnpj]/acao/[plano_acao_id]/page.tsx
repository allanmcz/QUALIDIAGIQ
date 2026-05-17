import { Suspense } from "react";
import { notFound } from "next/navigation";

import { PlanoAcaoFichaUnificadaPage } from "./PlanoAcaoFichaUnificadaPage";
import {
  parseCnpjParam,
  parsePlanoAcaoIdFromRoute,
} from "@/lib/dashboard/plano_acao_ficha_urls";

export default async function PlanoAcaoFichaRoute({
  params,
}: {
  params: Promise<{ cnpj: string; plano_acao_id: string }>;
}) {
  const { cnpj, plano_acao_id } = await params;
  const cnpjNorm = parseCnpjParam(cnpj);
  const planoId = parsePlanoAcaoIdFromRoute(plano_acao_id);
  if (!cnpjNorm || !planoId) {
    notFound();
  }

  return (
    <Suspense
      fallback={
        <div className="container py-10 text-muted-foreground">A carregar ficha da ação…</div>
      }
    >
      <PlanoAcaoFichaUnificadaPage cnpj14={cnpjNorm} planoAcaoId={planoId} />
    </Suspense>
  );
}
