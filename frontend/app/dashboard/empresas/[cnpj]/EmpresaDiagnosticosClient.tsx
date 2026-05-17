"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import { ArquivarEmpresaPainelButton } from "@/components/painel/ArquivarEmpresaPainelButton";
import { EmpresaPainelArquivoBanner } from "@/components/painel/EmpresaPainelArquivoBanner";
import { ExcluirCiclosElegiveisEmpresaButton } from "@/components/painel/ExcluirCiclosElegiveisEmpresaButton";
import { fetchEmpresaArquivoStatus } from "@/lib/api/arquivar_empresa_painel";
import { EmpresaComparacaoQuestionarioDialog } from "@/components/painel/empresa/EmpresaComparacaoQuestionarioDialog";
import { EmpresaDiagnosticosListaPainel } from "@/components/painel/empresa/EmpresaDiagnosticosListaPainel";
import { EmpresaQuadroImplantacaoTopo } from "@/components/painel/empresa/EmpresaQuadroImplantacaoTopo";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { temSessaoPainelParaApiCliente } from "@/lib/api/config";
import { fetchDiagnosticoDetalhe } from "@/lib/api/fetch_diagnostico_detalhe";
import type { DiagnosticoResumoApi } from "@/lib/api/lista_diagnosticos";
import { buildWizardUrlNovaDiagnosticoEmpresa } from "@/lib/dashboard/empresa_diagnostico_urls";
import { navegarRefazerDiagnosticoPainel } from "@/lib/dashboard/refazer_diagnostico_painel";
import { idDiagnosticoBaselineQuadroEmpresa } from "@/lib/painel/diagnostico_empresa_ordem";
import {
  MAX_DIAGNOSTICOS_COMPARACAO,
  MIN_DIAGNOSTICOS_COMPARACAO,
} from "@/lib/api/questionario_painel";
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
  const [listaPainel, setListaPainel] = useState<DiagnosticoResumoApi[] | null>(null);
  const [detalhesPorId, setDetalhesPorId] = useState<Record<string, DiagnosticoDetalheApi>>({});
  const [quadroCarregando, setQuadroCarregando] = useState(false);
  const [quadroErro, setQuadroErro] = useState<string | null>(null);
  const [selecaoComparacaoIds, setSelecaoComparacaoIds] = useState<string[]>([]);
  const [empresaArquivada, setEmpresaArquivada] = useState(false);
  const [msgOperacao, setMsgOperacao] = useState<string | null>(null);
  const [comparacaoAberta, setComparacaoAberta] = useState(false);

  const toggleSelecaoComparacao = useCallback((diagnosticoId: string, marcado: boolean) => {
    setSelecaoComparacaoIds((prev) => {
      if (marcado) {
        if (prev.includes(diagnosticoId)) return prev;
        if (prev.length >= MAX_DIAGNOSTICOS_COMPARACAO) return prev;
        return [...prev, diagnosticoId];
      }
      return prev.filter((id) => id !== diagnosticoId);
    });
  }, []);

  const baselineId = useMemo(
    () => (listaPainel?.length ? idDiagnosticoBaselineQuadroEmpresa(listaPainel) : null),
    [listaPainel],
  );

  const aoDiagnosticosPainel = useCallback((rows: DiagnosticoResumoApi[]) => {
    setListaPainel(rows);
  }, []);

  const aoDetalhesPrefetch = useCallback((detalhes: Record<string, DiagnosticoDetalheApi>) => {
    setDetalhesPorId((prev) => ({ ...prev, ...detalhes }));
  }, []);

  const aoDetalheAtualizado = useCallback((d: DiagnosticoDetalheApi) => {
    setDetalhesPorId((prev) => ({ ...prev, [d.id]: d }));
  }, []);

  const semSessao = !temSessaoPainelParaApiCliente();

  useEffect(() => {
    if (semSessao) return;
    let cancel = false;
    void fetchEmpresaArquivoStatus(cnpjNormalizado)
      .then((s) => {
        if (!cancel) setEmpresaArquivada(s.arquivado);
      })
      .catch(() => {
        if (!cancel) setEmpresaArquivada(false);
      });
    return () => {
      cancel = true;
    };
  }, [cnpjNormalizado, semSessao]);

  /** Garante GET do baseline se o prefetch da lista ainda não trouxe o detalhe. */
  useEffect(() => {
    if (!baselineId || semSessao) return;
    if (detalhesPorId[baselineId]) return;

    let cancel = false;
    setQuadroCarregando(true);
    setQuadroErro(null);
    void fetchDiagnosticoDetalhe(baselineId)
      .then((d) => {
        if (!cancel) aoDetalheAtualizado(d);
      })
      .catch((e) => {
        if (!cancel) {
          setQuadroErro(
            e instanceof Error ? e.message : "Não foi possível carregar o quadro de implantação da empresa.",
          );
        }
      })
      .finally(() => {
        if (!cancel) setQuadroCarregando(false);
      });
    return () => {
      cancel = true;
    };
  }, [baselineId, semSessao, detalhesPorId[baselineId ?? ""], aoDetalheAtualizado]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const hash = window.location.hash.replace(/^#/, "").trim();
    if (hash !== "empresa-quadro-implantacao-principal" && hash !== "empresa-implantacao-bloco") return;
    const timer = window.setTimeout(() => {
      document.getElementById(hash)?.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 400);
    return () => window.clearTimeout(timer);
  }, [listaPainel, detalhesPorId]);

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
                <ArquivarEmpresaPainelButton
                  cnpj14={cnpjNormalizado}
                  razaoSocial={tituloEmpresa}
                  arquivada={empresaArquivada}
                  variant="outline"
                  className="w-full sm:w-auto"
                  onConcluido={(mensagem) => {
                    setMsgOperacao(mensagem);
                    void fetchEmpresaArquivoStatus(cnpjNormalizado).then((s) =>
                      setEmpresaArquivada(s.arquivado),
                    );
                  }}
                />
                <ExcluirCiclosElegiveisEmpresaButton
                  cnpj14={cnpjNormalizado}
                  razaoSocial={tituloEmpresa}
                  variant="outline"
                  className="w-full sm:w-auto text-destructive hover:text-destructive"
                  onExcluido={(mensagem) => {
                    setMsgOperacao(mensagem);
                    router.refresh();
                  }}
                />
              </div>
              <p className="text-xs text-muted-foreground max-w-md sm:text-right">
                Plano e cronograma consolidados abrem no diagnóstico mais recente. Remova apenas ciclos não finalizados;
                arquivar oculta a empresa na listagem geral sem apagar evidências WORM.
              </p>
              {msgOperacao ? (
                <p className="text-xs text-primary max-w-md sm:text-right" role="status">
                  {msgOperacao}
                </p>
              ) : null}
            </div>
          )}
        </div>

        {!semSessao && empresaArquivada ? (
          <EmpresaPainelArquivoBanner
            cnpj14={cnpjNormalizado}
            razaoSocial={tituloEmpresa}
            onDesarquivada={(mensagem) => {
              setMsgOperacao(mensagem);
              setEmpresaArquivada(false);
            }}
          />
        ) : null}

        {!semSessao && (
          <div className="flex flex-col sm:flex-row flex-wrap gap-2">
            <Button
              type="button"
              className="w-full sm:w-auto"
              onClick={() =>
                navegarRefazerDiagnosticoPainel(
                  router,
                  buildWizardUrlNovaDiagnosticoEmpresa(cnpjNormalizado, tituloEmpresa),
                )
              }
            >
              Novo ciclo de diagnóstico
            </Button>
            <Button
              type="button"
              variant="outline"
              className="w-full sm:w-auto"
              disabled={selecaoComparacaoIds.length < MIN_DIAGNOSTICOS_COMPARACAO}
              onClick={() => setComparacaoAberta(true)}
            >
              Comparar questionário
              {selecaoComparacaoIds.length > 0
                ? ` (${selecaoComparacaoIds.length}/${MAX_DIAGNOSTICOS_COMPARACAO})`
                : ""}
            </Button>
          </div>
        )}

        {!semSessao ? (
          <Card className="mb-10 overflow-visible" id="painel-diagnosticos-empresa">
            <CardHeader className="pb-2">
              <CardTitle className="text-lg">Diagnósticos desta empresa no painel</CardTitle>
              <CardDescription>
                Cada linha é um ciclo. Marque até {MAX_DIAGNOSTICOS_COMPARACAO} linhas e use{" "}
                <strong className="font-medium text-foreground">Comparar questionário</strong> para ver a
                evolução das respostas. Use <strong className="font-medium text-foreground">Expandir</strong>{" "}
                para ranking (M05), matriz e M12.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <EmpresaDiagnosticosListaPainel
                cnpjNormalizado={cnpjNormalizado}
                usarExpandNaQuery
                onDiagnosticosAlterados={aoDiagnosticosPainel}
                onListaDetalheAtualizado={aoDetalheAtualizado}
                onDetalhesPrefetch={aoDetalhesPrefetch}
                selecaoComparacaoIds={selecaoComparacaoIds}
                onToggleSelecaoComparacao={toggleSelecaoComparacao}
              />
            </CardContent>
          </Card>
        ) : null}

        {!semSessao ? (
          <EmpresaQuadroImplantacaoTopo
            cnpj14={cnpjNormalizado}
            razaoSocialHint={tituloEmpresa}
            listaPainel={listaPainel}
            detalhesPorId={detalhesPorId}
            carregando={quadroCarregando}
            erro={quadroErro}
            onDataAtualizado={aoDetalheAtualizado}
          />
        ) : null}
      </div>

      <EmpresaComparacaoQuestionarioDialog
        open={comparacaoAberta}
        onOpenChange={setComparacaoAberta}
        diagnosticoIds={selecaoComparacaoIds}
        onLimparSelecao={() => setSelecaoComparacaoIds([])}
      />
    </div>
  );
}
