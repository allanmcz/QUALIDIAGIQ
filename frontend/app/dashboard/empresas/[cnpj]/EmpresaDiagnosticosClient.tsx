"use client";

import Link from "next/link";
import { useCallback, useMemo, useState } from "react";

import { EmpresaDiagnosticosListaPainel } from "@/components/painel/empresa/EmpresaDiagnosticosListaPainel";
import { Button } from "@/components/ui/button";
import { temSessaoPainelParaApiCliente } from "@/lib/api/config";
import type { DiagnosticoResumoApi } from "@/lib/api/lista_diagnosticos";
import { buildWizardUrlNovaDiagnosticoEmpresa } from "@/lib/dashboard/empresa_diagnostico_urls";

function mascaraCnpj14(d: string): string {
  const c = d.replace(/\D/g, "");
  if (c.length !== 14) return d;
  return c.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/, "$1.$2.$3/$4-$5");
}

function pickLatestDiagnosticId(rows: DiagnosticoResumoApi[]): string | null {
  if (!rows.length) return null;
  const sorted = [...rows].sort((a, b) => {
    const da = new Date(a.finalizado_em ?? a.criado_em).getTime();
    const db = new Date(b.finalizado_em ?? b.criado_em).getTime();
    return db - da;
  });
  return sorted[0]?.id ?? null;
}

export default function EmpresaDiagnosticosClient({
  cnpjNormalizado,
  razaoSocialHint,
}: {
  cnpjNormalizado: string;
  razaoSocialHint: string;
}) {
  /** Espelho da lista interior — cabeçalho e botão «Plano» sem GET duplicado. */
  const [listaPainel, setListaPainel] = useState<DiagnosticoResumoApi[] | null>(null);
  const aoDiagnosticosPainel = useCallback((rows: DiagnosticoResumoApi[]) => {
    setListaPainel(rows);
  }, []);

  const tituloEmpresa = useMemo(() => {
    const hint = razaoSocialHint.trim();
    if (hint.length >= 3) return hint;
    const primeiro = listaPainel?.[0]?.empresa_razao_social?.trim();
    if (primeiro && primeiro.length >= 3) return primeiro;
    return `Empresa · CNPJ ${mascaraCnpj14(cnpjNormalizado)}`;
  }, [razaoSocialHint, listaPainel, cnpjNormalizado]);

  const latestId = useMemo(
    () => (listaPainel?.length ? pickLatestDiagnosticId(listaPainel) : null),
    [listaPainel],
  );

  const semSessao = !temSessaoPainelParaApiCliente();

  const sublinhaCounts =
    listaPainel === null && !semSessao ? " · …" : listaPainel != null ? ` · ${listaPainel.length} diagnóstico(s) neste tenant` : "";

  return (
    <div className="container py-10">
      <div className="flex flex-col gap-6">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div className="space-y-1">
            <Link
              href="/dashboard/diagnosticos"
              className="text-sm text-primary hover:underline inline-block"
            >
              ← Voltar ao painel de diagnósticos
            </Link>
            <h1 className="text-2xl md:text-3xl font-bold tracking-tight">{tituloEmpresa}</h1>
            <p className="text-muted-foreground text-sm tabular-nums">
              CNPJ {mascaraCnpj14(cnpjNormalizado)}
              {semSessao ? "" : sublinhaCounts}
            </p>
          </div>
          {!semSessao && (
            <div className="flex flex-col gap-2 sm:items-end">
              <div className="flex flex-col xs:flex-row gap-2 w-full sm:w-auto">
                {latestId ? (
                  <Button variant="secondary" size="sm" className="w-full sm:w-auto" asChild>
                    <Link href={`/dashboard/diagnosticos/${latestId}#m06-cronograma-tabela-heading`}>
                      Plano de ação (empresa)
                    </Link>
                  </Button>
                ) : null}
                <Button variant="outline" size="sm" className="w-full sm:w-auto" asChild>
                  <Link href="/dashboard/privacidade">LGPD e direitos do titular</Link>
                </Button>
              </div>
              <p className="text-xs text-muted-foreground max-w-md sm:text-right">
                Plano e cronograma consolidados abrem no diagnóstico mais recente. LGPD: área do tenant
                (solicitações, portabilidade).
              </p>
            </div>
          )}
        </div>

        {!semSessao && (
          <div>
            <Button asChild className="w-full sm:w-auto">
              <Link href={buildWizardUrlNovaDiagnosticoEmpresa(cnpjNormalizado, tituloEmpresa)}>
                Novo Diagnóstico
              </Link>
            </Button>
          </div>
        )}

        <EmpresaDiagnosticosListaPainel
          cnpjNormalizado={cnpjNormalizado}
          usarExpandNaQuery
          onDiagnosticosAlterados={aoDiagnosticosPainel}
        />
      </div>
    </div>
  );
}
