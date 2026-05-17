"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Info } from "lucide-react";

import { ArquivarEmpresaPainelButton } from "@/components/painel/ArquivarEmpresaPainelButton";
import { EmpresaPainelArquivoBanner } from "@/components/painel/EmpresaPainelArquivoBanner";
import { ExcluirCiclosElegiveisEmpresaButton } from "@/components/painel/ExcluirCiclosElegiveisEmpresaButton";
import { fetchEmpresaArquivoStatus } from "@/lib/api/arquivar_empresa_painel";
import { EmpresaCicloEmFocoBar } from "@/components/painel/empresa/EmpresaCicloEmFocoBar";
import { EmpresaComparacaoQuestionarioDialog } from "@/components/painel/empresa/EmpresaComparacaoQuestionarioDialog";
import { EmpresaDiagnosticosListaPainel } from "@/components/painel/empresa/EmpresaDiagnosticosListaPainel";
import { EmpresaQuadroImplantacaoTopo } from "@/components/painel/empresa/EmpresaQuadroImplantacaoTopo";
import { DiagnosticoCronogramaM06Card } from "@/components/painel/empresa/DiagnosticoCronogramaM06Card";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { temSessaoPainelParaApiCliente } from "@/lib/api/config";
import { fetchDiagnosticoDetalhe } from "@/lib/api/fetch_diagnostico_detalhe";
import type { DiagnosticoResumoApi } from "@/lib/api/lista_diagnosticos";
import { QUERY_FICHA_SALVA } from "@/lib/dashboard/plano_acao_ficha_urls";
import {
  buildWizardUrlNovaDiagnosticoEmpresa,
  QUERY_EXPAND_DIAGNOSTICO,
} from "@/lib/dashboard/empresa_diagnostico_urls";
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

export default function EmpresaDiagnosticosClient({
  cnpjNormalizado,
  razaoSocialHint,
}: {
  cnpjNormalizado: string;
  razaoSocialHint: string;
}) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [listaPainel, setListaPainel] = useState<DiagnosticoResumoApi[] | null>(null);
  const [detalhesPorId, setDetalhesPorId] = useState<Record<string, DiagnosticoDetalheApi>>({});
  const [quadroCarregando, setQuadroCarregando] = useState(false);
  const [quadroErro, setQuadroErro] = useState<string | null>(null);
  const [selecaoComparacaoIds, setSelecaoComparacaoIds] = useState<string[]>([]);
  const [empresaArquivada, setEmpresaArquivada] = useState(false);
  const [listaRecarregarToken, setListaRecarregarToken] = useState(0);
  const [msgOperacao, setMsgOperacao] = useState<string | null>(null);
  const [comparacaoAberta, setComparacaoAberta] = useState(false);
  const [cicloEmFocoId, setCicloEmFocoId] = useState<string | null>(
    () => searchParams.get(QUERY_EXPAND_DIAGNOSTICO)?.trim() || null,
  );

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

  const aoEmpresaDesarquivada = useCallback((mensagem: string) => {
    setMsgOperacao(mensagem);
    setEmpresaArquivada(false);
    setListaRecarregarToken((t) => t + 1);
    void fetchEmpresaArquivoStatus(cnpjNormalizado)
      .then((s) => setEmpresaArquivada(s.arquivado))
      .catch(() => setEmpresaArquivada(false));
  }, [cnpjNormalizado]);

  const semSessao = !temSessaoPainelParaApiCliente();

  useEffect(() => {
    if (searchParams.get(QUERY_FICHA_SALVA) !== "1") return;
    setMsgOperacao("Alterações da ficha gravadas com sucesso.");
    const url = new URL(window.location.href);
    url.searchParams.delete(QUERY_FICHA_SALVA);
    const qs = url.searchParams.toString();
    const path = `${url.pathname}${qs ? `?${qs}` : ""}${url.hash}`;
    router.replace(path, { scroll: false });
  }, [searchParams, router]);

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
    const expandId = searchParams.get(QUERY_EXPAND_DIAGNOSTICO)?.trim();
    if (expandId) setCicloEmFocoId(expandId);
  }, [searchParams]);

  useEffect(() => {
    if (!cicloEmFocoId || semSessao || detalhesPorId[cicloEmFocoId]) return;
    void fetchDiagnosticoDetalhe(cicloEmFocoId).then(aoDetalheAtualizado).catch(() => undefined);
  }, [cicloEmFocoId, semSessao, detalhesPorId, aoDetalheAtualizado]);

  const cicloEmFocoDetalhe = cicloEmFocoId ? detalhesPorId[cicloEmFocoId] : undefined;
  const cicloEmFocoResumo = useMemo(
    () => listaPainel?.find((d) => d.id === cicloEmFocoId) ?? null,
    [listaPainel, cicloEmFocoId],
  );
  const baselineDetalhe = baselineId ? detalhesPorId[baselineId] : undefined;

  useEffect(() => {
    if (typeof window === "undefined") return;
    const hash = window.location.hash.replace(/^#/, "").trim();
    if (
      hash !== "empresa-quadro-implantacao-principal" &&
      hash !== "empresa-implantacao-bloco" &&
      hash !== "empresa-kanban-plano-titulo"
    ) {
      return;
    }
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
            <div className="flex w-full flex-col gap-2 sm:w-auto sm:items-end">
              <div
                className="flex w-full flex-nowrap items-center justify-end gap-2 overflow-x-auto"
                role="toolbar"
                aria-label="Ações da empresa no painel"
              >
                <Button variant="outline" size="sm" className="shrink-0 whitespace-nowrap" asChild>
                  <Link href="/dashboard/privacidade">LGPD e direitos do titular</Link>
                </Button>
                <ArquivarEmpresaPainelButton
                  cnpj14={cnpjNormalizado}
                  razaoSocial={tituloEmpresa}
                  arquivada={empresaArquivada}
                  variant="outline"
                  size="sm"
                  className="shrink-0 whitespace-nowrap"
                  onConcluido={(mensagem) => {
                    if (empresaArquivada) {
                      aoEmpresaDesarquivada(mensagem);
                      return;
                    }
                    setMsgOperacao(mensagem);
                    void fetchEmpresaArquivoStatus(cnpjNormalizado).then((s) => {
                      setEmpresaArquivada(s.arquivado);
                      if (!s.arquivado) setListaRecarregarToken((t) => t + 1);
                    });
                  }}
                />
                <ExcluirCiclosElegiveisEmpresaButton
                  cnpj14={cnpjNormalizado}
                  razaoSocial={tituloEmpresa}
                  variant="outline"
                  size="sm"
                  className="shrink-0 whitespace-nowrap text-destructive hover:text-destructive"
                  onExcluido={(mensagem) => {
                    setMsgOperacao(mensagem);
                    router.refresh();
                  }}
                />
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 shrink-0 text-muted-foreground"
                      aria-label="Ajuda sobre plano consolidado, remover ciclos e arquivar empresa"
                    >
                      <Info className="h-4 w-4" aria-hidden />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent
                    side="bottom"
                    align="end"
                    className="max-w-md text-left text-xs leading-relaxed"
                  >
                    Plano e cronograma consolidados abrem no diagnóstico mais recente. Remova apenas ciclos não
                    finalizados; arquivar oculta a empresa na listagem geral sem apagar evidências WORM.
                  </TooltipContent>
                </Tooltip>
              </div>
              {msgOperacao ? (
                <p
                  className={
                    msgOperacao.includes("ficha gravadas")
                      ? "text-sm max-w-md sm:text-right border rounded-md p-2 border-emerald-600/40 bg-emerald-500/10 text-emerald-900 dark:text-emerald-200"
                      : "text-xs text-primary max-w-md sm:text-right"
                  }
                  role="status"
                >
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
            onDesarquivada={aoEmpresaDesarquivada}
          />
        ) : null}

        {!semSessao && cicloEmFocoDetalhe ? (
          <EmpresaCicloEmFocoBar detalhe={cicloEmFocoDetalhe} resumo={cicloEmFocoResumo} />
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
                para ranking (M05), matriz, M12 e explicação IA. Gaps consolidados, plano de implantação e
                cronograma ficam nos blocos abaixo.
              </CardDescription>
            </CardHeader>
            <CardContent className="overflow-visible">
              <EmpresaDiagnosticosListaPainel
                cnpjNormalizado={cnpjNormalizado}
                recarregarToken={listaRecarregarToken}
                usarExpandNaQuery
                onDiagnosticosAlterados={aoDiagnosticosPainel}
                onListaDetalheAtualizado={aoDetalheAtualizado}
                onDetalhesPrefetch={aoDetalhesPrefetch}
                selecaoComparacaoIds={selecaoComparacaoIds}
                onToggleSelecaoComparacao={toggleSelecaoComparacao}
                onLinhaAbertaIdChange={setCicloEmFocoId}
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

        {!semSessao && baselineDetalhe?.cronograma?.length ? (
          <DiagnosticoCronogramaM06Card cronograma={baselineDetalhe.cronograma} />
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
