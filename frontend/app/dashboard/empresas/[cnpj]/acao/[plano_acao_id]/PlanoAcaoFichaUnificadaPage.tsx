"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

import { PlanoAcaoFichaUnificadaClient } from "@/components/painel/empresa/PlanoAcaoFichaUnificadaClient";
import {
  buildVoltaEmpresaHref,
  parseFichaSearchParams,
} from "@/lib/dashboard/plano_acao_ficha_urls";
import {
  fetchDiagnosticosResumoTodasPaginasPorEmpresa,
  type DiagnosticoResumoApi,
} from "@/lib/api/lista_diagnosticos";

type Props = {
  cnpj14: string;
  planoAcaoId: string;
};

export function PlanoAcaoFichaUnificadaPage({ cnpj14, planoAcaoId }: Props) {
  const spClient = useSearchParams();
  const parsed = parseFichaSearchParams(spClient);

  const diagnosticoId = parsed.diagnosticoId;
  const razaoSocial = parsed.razaoSocial;
  const [lista, setLista] = useState<DiagnosticoResumoApi[] | null>(null);

  useEffect(() => {
    void fetchDiagnosticosResumoTodasPaginasPorEmpresa(cnpj14)
      .then(setLista)
      .catch(() => setLista([]));
  }, [cnpj14]);

  if (!diagnosticoId) {
    return (
      <div className="container py-10 space-y-4">
        <Link
          href={buildVoltaEmpresaHref(cnpj14, razaoSocial)}
          className="text-sm text-primary hover:underline"
        >
          ← Voltar à empresa
        </Link>
        <p className="text-destructive" role="alert">
          Parâmetro obrigatório ausente: <code>diagnostico_id</code> na URL (ciclo de referência do
          quadro).
        </p>
      </div>
    );
  }

  return (
    <PlanoAcaoFichaUnificadaClient
      cnpj14={cnpj14}
      planoAcaoId={planoAcaoId}
      diagnosticoId={diagnosticoId}
      razaoSocialHint={razaoSocial}
      listaPainel={lista}
    />
  );
}
