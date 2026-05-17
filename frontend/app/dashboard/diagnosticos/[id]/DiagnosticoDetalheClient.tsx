"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { fetchDiagnosticoDetalhe } from "@/lib/api/fetch_diagnostico_detalhe";
import { buildEmpresaDiagnosticosHref } from "@/lib/dashboard/empresa_diagnostico_urls";

/**
 * Redireciona `/dashboard/diagnosticos/[id]` → vista unificada por CNPJ com `?expand=`.
 */
export default function DiagnosticoDetalheClient({ id }: { id: string }) {
  const router = useRouter();
  const [erro, setErro] = useState<string | null>(null);

  useEffect(() => {
    let cancel = false;
    void fetchDiagnosticoDetalhe(id)
      .then((d) => {
        if (cancel) return;
        const cnpj = (d.empresa_cnpj ?? "").replace(/\D/g, "").trim();
        if (cnpj.length !== 14) {
          setErro("Este diagnóstico não tem CNPJ associado — abra-o na listagem geral.");
          return;
        }
        const destino = buildEmpresaDiagnosticosHref(cnpj, d.empresa_razao_social, {
          expandDiagnosticoId: d.id,
        });
        router.replace(destino);
      })
      .catch(() => {
        if (!cancel) setErro("Não foi possível localizar este diagnóstico.");
      });
    return () => {
      cancel = true;
    };
  }, [id, router]);

  if (erro) {
    return (
      <div className="container py-10 space-y-4">
        <p className="text-sm text-destructive" role="alert">
          {erro}
        </p>
        <Link href="/dashboard/diagnosticos" className="text-sm text-primary hover:underline">
          ← Voltar ao painel de diagnósticos
        </Link>
      </div>
    );
  }

  return (
    <div className="container py-10 text-muted-foreground" role="status">
      A redirecionar para a vista da empresa…
    </div>
  );
}
