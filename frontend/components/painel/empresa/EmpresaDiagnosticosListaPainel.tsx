"use client";

/**
 * Lista de ciclos (diagnósticos) da mesma PJ no tenant — M05/M12 na expansão.
 * Partilhado entre `/dashboard/empresas/[cnpj]` e `/dashboard/diagnosticos/[id]`.
 */

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import type { ReactNode } from "react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ChevronDown, RefreshCw } from "lucide-react";

import EmpresaDiagnosticoExpandedPanel from "@/components/painel/empresa/EmpresaDiagnosticoExpandedPanel";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { fetchDiagnosticoDetalhe } from "@/lib/api/fetch_diagnostico_detalhe";
import {
  DIAGNOSTICOS_RESUMO_PAGE_SIZE_MAX,
  fetchDiagnosticosResumo,
  fetchDiagnosticosResumoTodasPaginasPorEmpresa,
  type DiagnosticoResumoApi,
} from "@/lib/api/lista_diagnosticos";
import { temSessaoPainelParaApiCliente } from "@/lib/api/config";
import { buildWizardUrlNovaDiagnosticoEmpresa } from "@/lib/dashboard/empresa_diagnostico_urls";
import { navegarRefazerDiagnosticoPainel } from "@/lib/dashboard/refazer_diagnostico_painel";
import type { DiagnosticoDetalheApi } from "@/types/diagnostico_detalhe";

const PREFETCH_CONCORRENCIA = 4;

const GRID_COLS_EMPRESA =
  "sm:grid-cols-[minmax(0,1fr)_5rem_7rem_6rem_minmax(11rem,13rem)]";

export type EmpresaDiagnosticosListaPainelProps = {
  cnpjNormalizado: string;
  /** `/dashboard/empresas/...?expand=` — só activo quando `true`. */
  usarExpandNaQuery?: boolean;
  /** Ao carregar a lista, expande esta linha (ex.: ficha actual). */
  expandirDiagnosticoId?: string | null;
  /** Evita esperar prefetch para o ciclo já mostrado na página pai. */
  diagnosticoSemeado?: DiagnosticoDetalheApi | null;
  /** Texto opcional antes da lista (titulação da secção na ficha única). */
  cabecalhoSlot?: ReactNode;
  /** Chamado sempre que o array de diagnósticos muda no tenant (lista carregada ou vazia). */
  onDiagnosticosAlterados?: (rows: DiagnosticoResumoApi[]) => void;
};

export function EmpresaDiagnosticosListaPainel({
  cnpjNormalizado,
  usarExpandNaQuery = false,
  expandirDiagnosticoId = null,
  diagnosticoSemeado = null,
  cabecalhoSlot,
  onDiagnosticosAlterados,
}: EmpresaDiagnosticosListaPainelProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [diagnosticos, setDiagnosticos] = useState<DiagnosticoResumoApi[] | null>(null);
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const [detalhesPorId, setDetalhesPorId] = useState<Record<string, DiagnosticoDetalheApi>>(() =>
    diagnosticoSemeado ? { [diagnosticoSemeado.id]: diagnosticoSemeado } : {},
  );
  const [prefetchErro, setPrefetchErro] = useState<string | null>(null);
  const [linhaAbertaId, setLinhaAbertaId] = useState<string | null>(null);

  /** Abre ciclo vindos da página empresa (`?expand=`) sem conflitar com fecho manual pela mesma deps. */
  const expandJaAplicadoChaveRef = useRef<string | null>(null);

  useEffect(() => {
    if (!diagnosticoSemeado) return;
    setDetalhesPorId((prev) => ({ ...prev, [diagnosticoSemeado.id]: diagnosticoSemeado }));
  }, [diagnosticoSemeado]);

  /** Deep link `?expand=` (view por CNPJ). */
  useEffect(() => {
    if (!usarExpandNaQuery) return;
    const expandId = searchParams.get("expand")?.trim();
    if (!expandId || !diagnosticos?.some((d) => d.id === expandId)) return;
    setLinhaAbertaId(expandId);
  }, [usarExpandNaQuery, searchParams, diagnosticos]);

  /**
   * Ficha única: expande o ciclo actual uma vez quando a lista chega (query sem `expand` tem prioridade vazia).
   */
  useEffect(() => {
    if (usarExpandNaQuery && searchParams.get("expand")?.trim()) return;
    const sid = expandirDiagnosticoId?.trim();
    if (!sid || !diagnosticos?.some((d) => d.id === sid)) return;
    const chave = `${cnpjNormalizado}:${sid}`;
    if (expandJaAplicadoChaveRef.current === chave) return;
    setLinhaAbertaId(sid);
    expandJaAplicadoChaveRef.current = chave;
  }, [usarExpandNaQuery, searchParams, diagnosticos, expandirDiagnosticoId, cnpjNormalizado]);

  useEffect(() => {
    expandJaAplicadoChaveRef.current = null;
  }, [cnpjNormalizado, expandirDiagnosticoId]);

  useEffect(() => {
    if (!linhaAbertaId || typeof window === "undefined") return;
    const hash = window.location.hash.replace(/^#/, "").trim();
    if (!hash) return;
    const timer = window.setTimeout(() => {
      document.getElementById(hash)?.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 350);
    return () => window.clearTimeout(timer);
  }, [linhaAbertaId]);

  useEffect(() => {
    let cancel = false;
    async function load() {
      if (!temSessaoPainelParaApiCliente()) {
        setDiagnosticos([]);
        return;
      }
      setCarregando(true);
      setErro(null);
      try {
        let rows = await fetchDiagnosticosResumoTodasPaginasPorEmpresa(cnpjNormalizado);
        if (rows.length === 0) {
          const todos = await fetchDiagnosticosResumo(DIAGNOSTICOS_RESUMO_PAGE_SIZE_MAX, 0);
          rows = todos.filter(
            (d) => (d.empresa_cnpj ?? "").replace(/\D/g, "") === cnpjNormalizado,
          );
        }
        if (!cancel) setDiagnosticos(rows);
      } catch (e) {
        if (!cancel) setErro(e instanceof Error ? e.message : "Falha ao carregar diagnósticos.");
      } finally {
        if (!cancel) setCarregando(false);
      }
    }
    void load();
    return () => {
      cancel = true;
    };
  }, [cnpjNormalizado]);

  useEffect(() => {
    if (!diagnosticos?.length || !temSessaoPainelParaApiCliente()) return;
    let cancel = false;
    const ids = diagnosticos.map((d) => d.id);
    setPrefetchErro(null);

    (async () => {
      const next: Record<string, DiagnosticoDetalheApi> = {};
      for (let i = 0; i < ids.length; i += PREFETCH_CONCORRENCIA) {
        if (cancel) return;
        const chunk = ids.slice(i, i + PREFETCH_CONCORRENCIA);
        const settled = await Promise.allSettled(chunk.map((id) => fetchDiagnosticoDetalhe(id)));
        if (cancel) return;
        settled.forEach((r, j) => {
          const id = chunk[j];
          if (r.status === "fulfilled") next[id] = r.value;
        });
      }
      if (!cancel) {
        setDetalhesPorId((prev) => ({ ...prev, ...next }));
      }
    })().catch(() => {
      if (!cancel) setPrefetchErro("Pré-carga de scores para ranking global incompleta — expanda uma linha.");
    });

    return () => {
      cancel = true;
    };
  }, [diagnosticos]);

  useEffect(() => {
    if (diagnosticos === null) return;
    onDiagnosticosAlterados?.(diagnosticos);
  }, [diagnosticos, onDiagnosticosAlterados]);

  const detalhesListaAgregacao = useMemo(() => Object.values(detalhesPorId), [detalhesPorId]);

  const aoAtualizarDetalhe = useCallback((d: DiagnosticoDetalheApi) => {
    setDetalhesPorId((prev) => ({ ...prev, [d.id]: d }));
  }, []);

  const aoRefazerDiagnostico = useCallback(
    (razaoSocial: string) => {
      navegarRefazerDiagnosticoPainel(
        router,
        buildWizardUrlNovaDiagnosticoEmpresa(cnpjNormalizado, razaoSocial),
      );
    },
    [router, cnpjNormalizado],
  );

  const daEmpresa = diagnosticos ?? [];
  const semSessao = !temSessaoPainelParaApiCliente();

  return (
    <div className="flex flex-col gap-6">
      {cabecalhoSlot}

      {semSessao && (
        <div className="rounded-lg border border-amber-500/40 bg-amber-500/10 p-4 text-sm">
          Para ver e criar diagnósticos faça{" "}
          <Link href="/login" className="text-primary font-medium underline">
            login
          </Link>
          .
        </div>
      )}

      {erro && (
        <div
          className="rounded-lg border border-destructive/40 bg-destructive/10 p-4 text-sm text-destructive"
          role="alert"
        >
          {erro}
        </div>
      )}

      {prefetchErro && !erro && (
        <p className="text-sm text-amber-700 dark:text-amber-400" role="status">
          {prefetchErro}
        </p>
      )}

      {!semSessao &&
        !carregando &&
        diagnosticos !== null &&
        daEmpresa.length > 0 &&
        Object.keys(detalhesPorId).length < daEmpresa.length &&
        !prefetchErro && (
          <p className="text-sm text-muted-foreground" aria-live="polite">
            A consolidar ranking global… ({Object.keys(detalhesPorId).length}/{daEmpresa.length}{" "}
            diagnósticos com detalhe carregado)
          </p>
        )}

      {!semSessao && carregando && (
        <p className="text-muted-foreground text-sm" aria-live="polite">
          A carregar diagnósticos desta empresa…
        </p>
      )}

      {!semSessao && !erro && !carregando && diagnosticos !== null && daEmpresa.length === 0 && (
        <p className="text-muted-foreground text-sm max-w-2xl leading-relaxed">
          Nenhum diagnóstico encontrado para este CNPJ neste tenant (ou os registos ainda não incluem{" "}
          <span className="font-mono tabular-nums">{cnpjNormalizado}</span>).
        </p>
      )}

      {!semSessao && !carregando && daEmpresa.length > 0 && (
        <div className="rounded-xl border bg-card/40 overflow-hidden">
          <div
            className={`hidden sm:grid ${GRID_COLS_EMPRESA} sm:gap-3 sm:items-center px-4 py-3 text-xs font-semibold uppercase tracking-wide text-muted-foreground border-b bg-muted/30`}
          >
            <span>Empresa / ciclo</span>
            <span className="text-center">Score</span>
            <span className="text-center">Estado</span>
            <span className="text-center">Data</span>
            <span className="text-center">Ações</span>
          </div>
          <ul className="divide-y" aria-label="Diagnósticos desta empresa no tenant">
            {daEmpresa.map((diag) => {
              const score = diag.score_geral;
              const pct = score != null ? Math.min(100, Math.max(0, score)) : null;
              const quando = new Date(diag.finalizado_em ?? diag.criado_em).toLocaleDateString("pt-BR", {
                day: "2-digit",
                month: "2-digit",
                year: "numeric",
              });
              const aberto = linhaAbertaId === diag.id;
              const detailHref = `/dashboard/diagnosticos/${diag.id}`;

              return (
                <li key={diag.id}>
                  <div
                    className={`px-3 py-4 sm:px-4 space-y-3 sm:space-y-0 sm:grid ${GRID_COLS_EMPRESA} sm:gap-3 sm:items-center`}
                  >
                    <div className="min-w-0">
                      <Link
                        href={detailHref}
                        className="font-medium text-foreground hover:text-primary hover:underline line-clamp-2"
                      >
                        {diag.empresa_razao_social}
                      </Link>
                      <p className="text-xs text-muted-foreground mt-0.5 truncate">
                        {diag.numero_interno_grupo != null ? (
                          <>
                            Nº interno <span className="tabular-nums font-medium">{diag.numero_interno_grupo}</span>
                          </>
                        ) : (
                          <span className="tabular-nums">Nº interno —</span>
                        )}
                      </p>
                    </div>
                    <div className="flex items-center justify-between gap-2 sm:block sm:text-center tabular-nums text-sm">
                      <span className="text-xs text-muted-foreground sm:hidden">Score</span>
                      <span>{pct != null ? `${pct.toFixed(1)}` : "—"}</span>
                    </div>
                    <div className="flex items-center justify-between gap-2 sm:flex sm:justify-center">
                      <span className="text-xs text-muted-foreground sm:hidden">Estado</span>
                      <Badge variant={diag.plano === "avancado" ? "default" : "secondary"}>
                        {diag.status === "finalizado" ? "Finalizado" : diag.status}
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between gap-2 sm:block sm:text-center text-sm text-muted-foreground">
                      <span className="text-xs sm:hidden">Data</span>
                      <span>{quando}</span>
                    </div>
                    <div className="flex flex-col gap-1.5 w-full sm:items-end">
                      <div className="flex flex-wrap gap-1.5 w-full justify-end">
                        {diag.plano === "avancado" ? (
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            className="gap-1.5 h-8 text-xs shrink-0"
                            title="Novo ciclo no assistente (sem rascunho local)"
                            onClick={() => aoRefazerDiagnostico(diag.empresa_razao_social)}
                          >
                            <RefreshCw className="h-3.5 w-3.5 shrink-0" aria-hidden />
                            Refazer diagnóstico
                          </Button>
                        ) : null}
                        <Button
                          type="button"
                          variant={aberto ? "secondary" : "outline"}
                          size="sm"
                          className="gap-1.5 shrink-0"
                          aria-expanded={aberto}
                          aria-controls={`empresa-expand-${diag.id}`}
                          onClick={() =>
                            setLinhaAbertaId((cur) => (cur === diag.id ? null : diag.id))
                          }
                        >
                          <ChevronDown
                            className={`h-4 w-4 shrink-0 transition-transform ${aberto ? "rotate-180" : ""}`}
                            aria-hidden
                          />
                          {aberto ? "Fechar" : "Expandir"}
                        </Button>
                      </div>
                    </div>
                  </div>

                  {aberto ? (
                    <div id={`empresa-expand-${diag.id}`} className="border-t bg-muted/10">
                      <EmpresaDiagnosticoExpandedPanel
                        diagnosticoId={diag.id}
                        detalhePrecarregado={detalhesPorId[diag.id] ?? null}
                        detalhesEmpresaParaAgregado={detalhesListaAgregacao}
                        resumosEmpresa={daEmpresa}
                        onDetalheAtualizado={aoAtualizarDetalhe}
                      />
                    </div>
                  ) : null}
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </div>
  );
}
