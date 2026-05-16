"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import { ExcluirEmpresaPainelButton } from "@/components/painel/ExcluirEmpresaPainelButton";
import { EmpresaImplantacaoResumoDepartamentosCard } from "@/components/painel/empresa/EmpresaImplantacaoResumoDepartamentosCard";
import { EmpresaDiagnosticosListaPainel } from "@/components/painel/empresa/EmpresaDiagnosticosListaPainel";
import { QuadroImplantacaoGrid } from "@/components/painel/empresa/QuadroImplantacaoGrid";
import { Button } from "@/components/ui/button";
import { temSessaoPainelParaApiCliente } from "@/lib/api/config";
import { fetchDiagnosticoDetalhe } from "@/lib/api/fetch_diagnostico_detalhe";
import type { DiagnosticoResumoApi } from "@/lib/api/lista_diagnosticos";
import { buildWizardUrlNovaDiagnosticoEmpresa } from "@/lib/dashboard/empresa_diagnostico_urls";
import {
  idDiagnosticoMaisAntigoEmpresa,
  quadroImplantacaoEditavel,
} from "@/lib/painel/diagnostico_empresa_ordem";
import type { DiagnosticoDetalheApi } from "@/types/diagnostico_detalhe";

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
  const router = useRouter();
  /** Espelho da lista interior — cabeçalho e botão «Plano» sem GET duplicado. */
  const [listaPainel, setListaPainel] = useState<DiagnosticoResumoApi[] | null>(null);
  const [quadroEmpresaDetalhe, setQuadroEmpresaDetalhe] = useState<DiagnosticoDetalheApi | null>(null);

  const primeiroDiagId = useMemo(
    () => (listaPainel?.length ? idDiagnosticoMaisAntigoEmpresa(listaPainel) : null),
    [listaPainel],
  );

  const aoDiagnosticosPainel = useCallback((rows: DiagnosticoResumoApi[]) => {
    setListaPainel(rows);
  }, []);

  const syncQuadroTopo = useCallback(
    (d: DiagnosticoDetalheApi) => {
      if (primeiroDiagId && d.id === primeiroDiagId) setQuadroEmpresaDetalhe(d);
    },
    [primeiroDiagId],
  );

  const semSessao = !temSessaoPainelParaApiCliente();

  useEffect(() => {
    if (!primeiroDiagId || semSessao) {
      setQuadroEmpresaDetalhe(null);
      return;
    }
    let cancel = false;
    void fetchDiagnosticoDetalhe(primeiroDiagId)
      .then((d) => {
        if (!cancel) setQuadroEmpresaDetalhe(d);
      })
      .catch(() => {
        if (!cancel) setQuadroEmpresaDetalhe(null);
      });
    return () => {
      cancel = true;
    };
  }, [primeiroDiagId, semSessao]);

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

  const sublinhaCounts =
    listaPainel === null && !semSessao ? " · …" : listaPainel != null ? ` · ${listaPainel.length} diagnóstico(s) no painel` : "";

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
                <ExcluirEmpresaPainelButton
                  cnpj14={cnpjNormalizado}
                  razaoSocial={tituloEmpresa}
                  variant="outline"
                  className="w-full sm:w-auto text-destructive hover:text-destructive"
                  onExcluido={() => {
                    router.push("/dashboard/diagnosticos");
                  }}
                />
              </div>
              <p className="text-xs text-muted-foreground max-w-md sm:text-right">
                Plano e cronograma consolidados abrem no diagnóstico mais recente. A área LGPD reúne solicitações e
                portabilidade dos dados.
              </p>
            </div>
          )}
        </div>

        {!semSessao && (
          <div>
            <Button asChild className="w-full sm:w-auto">
              <Link href={buildWizardUrlNovaDiagnosticoEmpresa(cnpjNormalizado, tituloEmpresa)}>
                Novo ciclo de diagnóstico
              </Link>
            </Button>
          </div>
        )}

        {!semSessao && listaPainel && listaPainel.length > 0 && quadroEmpresaDetalhe && (
          <div className="space-y-6">
            <div>
              <h2 className="text-lg font-semibold tracking-tight">Quadro de implantação da empresa</h2>
              <p className="text-sm text-muted-foreground mt-1 max-w-3xl">
                <strong className="font-medium text-foreground">Um quadro por empresa</strong> para o mesmo CNPJ:
                prazos meta e notas do consultor aplicam-se à implantação global, não ao ciclo individual. Na
                tabela abaixo usa-se o plano de ações de referência; em cada linha da lista,{" "}
                <strong className="font-medium text-foreground">Expandir</strong> continua a mostrar só matriz,
                ranking e M12 daquele diagnóstico.
              </p>
            </div>
            <EmpresaImplantacaoResumoDepartamentosCard data={quadroEmpresaDetalhe} />
            <QuadroImplantacaoGrid
              diagnosticoId={quadroEmpresaDetalhe.id}
              data={quadroEmpresaDetalhe}
              editavel={quadroImplantacaoEditavel(quadroEmpresaDetalhe.id, listaPainel, quadroEmpresaDetalhe.status)}
              avisoSomenteLeitura={
                !quadroImplantacaoEditavel(
                  quadroEmpresaDetalhe.id,
                  listaPainel,
                  quadroEmpresaDetalhe.status,
                ) && quadroEmpresaDetalhe.status === "finalizado"
                  ? "Quadro da empresa em consulta: a edição fica concentrada no ciclo de referência da empresa. Neste diagnóstico, use a visualização apenas para acompanhamento."
                  : undefined
              }
              onDataAtualizado={syncQuadroTopo}
              id="empresa-quadro-implantacao-principal"
            />
          </div>
        )}

        <EmpresaDiagnosticosListaPainel
          cnpjNormalizado={cnpjNormalizado}
          usarExpandNaQuery
          onDiagnosticosAlterados={aoDiagnosticosPainel}
          onListaDetalheAtualizado={syncQuadroTopo}
        />
      </div>
    </div>
  );
}
