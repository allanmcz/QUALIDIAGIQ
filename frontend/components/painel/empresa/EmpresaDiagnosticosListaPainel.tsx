"use client";

/**
 * Lista de diagnósticos da mesma PJ no tenant — M05/M12 na expansão.
 * Partilhado entre `/dashboard/empresas/[cnpj]` e `/dashboard/diagnosticos/[id]`.
 */

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import type { ReactNode } from "react";
import {
  startTransition,
  useCallback,
  useEffect,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { createPortal } from "react-dom";
import { ChevronDown, RefreshCw } from "lucide-react";

import EmpresaDiagnosticoExpandedPanel from "@/components/painel/empresa/EmpresaDiagnosticoExpandedPanel";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  fetchDiagnosticoDetalhe,
  hrefRelatorioPdfAbsoluto,
} from "@/lib/api/fetch_diagnostico_detalhe";
import {
  abrirPdfQuestionarioDiagnostico,
  MAX_DIAGNOSTICOS_COMPARACAO,
} from "@/lib/api/questionario_painel";
import {
  fetchDiagnosticosResumoTodasPaginasPorEmpresa,
  type DiagnosticoResumoApi,
} from "@/lib/api/lista_diagnosticos";
import { patchPainelEstadoCicloDiagnostico } from "@/lib/api/patch_painel_estado_ciclo";
import { hrefPrivacidadePainel } from "@/lib/painel/privacidade_diagnostico_query";
import { temSessaoPainelParaApiCliente } from "@/lib/api/config";
import { buildWizardUrlNovaDiagnosticoEmpresa } from "@/lib/dashboard/empresa_diagnostico_urls";
import { navegarRefazerDiagnosticoPainel } from "@/lib/dashboard/refazer_diagnostico_painel";
import {
  PAINEL_ESTADO_CICLO_VALORES,
  type PainelEstadoCicloApi,
  rotuloPainelEstadoCiclo,
} from "@/lib/painel/painel_estado_ciclo_labels";
import type { DiagnosticoDetalheApi } from "@/types/diagnostico_detalhe";


/** Âncoras na ficha expandida — só abrem a linha com hash (não auto-expandir ao carregar). */
const HASHES_QUE_ABREM_LINHA = new Set([
  "diag-explicacao-score-llm",
  "empresa-m12-autoconf",
  "diag-ranking-gaps-heading",
  "empresa-matriz-impacto",
]);

const GRID_COLS_EMPRESA =
  "sm:grid-cols-[minmax(0,1fr)_5rem_7rem_6rem_minmax(11rem,13rem)]";

const GRID_COLS_EMPRESA_COM_SELECAO =
  "sm:grid-cols-[2.25rem_minmax(0,1fr)_5rem_7rem_6rem_minmax(11rem,13rem)]";

/** Garante linha na grelha quando o GET por CNPJ omite o registo em vista (ex.: `empresa_cnpj` vazio na lista). */
function resumoApiDesdeDetalheSemeado(d: DiagnosticoDetalheApi): DiagnosticoResumoApi {
  const criado =
    (d.criado_em && String(d.criado_em).trim()) || "1970-01-01T00:00:00.000Z";
  const cnpj = (d.empresa_cnpj ?? "").replace(/\D/g, "").trim();
  return {
    id: d.id,
    empresa_razao_social: d.empresa_razao_social,
    ...(cnpj.length === 14 ? { empresa_cnpj: cnpj } : {}),
    status: d.status,
    plano: d.plano,
    score_geral: d.score?.score_geral?.valor ?? null,
    criado_em: criado,
    finalizado_em: d.finalizado_em ?? null,
    relatorio_pdf_url: d.relatorio_pdf_url,
    versao_otimista: d.versao_otimista ?? null,
    painel_estado_ciclo: d.painel_estado_ciclo ?? null,
  };
}

export type EmpresaDiagnosticosListaPainelProps = {
  cnpjNormalizado: string;
  /** `/dashboard/empresas/...?expand=` — só activo quando `true`. */
  usarExpandNaQuery?: boolean;
  /**
   * Diagnóstico em foco na ficha `/dashboard/diagnosticos/[id]` — usado só com âncora (#)
   * ou `?expand=` (empresa); não expande a linha ao abrir a página.
   */
  expandirDiagnosticoId?: string | null;
  /** Evita esperar prefetch para o ciclo já mostrado na página pai. */
  diagnosticoSemeado?: DiagnosticoDetalheApi | null;
  /** Texto opcional antes da lista (titulação da secção na ficha única). */
  cabecalhoSlot?: ReactNode;
  /** Chamado sempre que o array de diagnósticos muda no tenant (lista carregada ou vazia). */
  onDiagnosticosAlterados?: (rows: DiagnosticoResumoApi[]) => void;
  /** Após mutação de GET detalhe ou PATCH (ex.: sincronizar quadro global da página empresa). */
  onListaDetalheAtualizado?: (d: DiagnosticoDetalheApi) => void;
  /** Pré-carga em lote dos detalhes (quadro no topo da página empresa). */
  onDetalhesPrefetch?: (detalhes: Record<string, DiagnosticoDetalheApi>) => void;
  /** Coluna de checkboxes para comparar questionário entre ciclos. */
  selecaoComparacaoIds?: string[];
  onToggleSelecaoComparacao?: (diagnosticoId: string, marcado: boolean) => void;
};

export function EmpresaDiagnosticosListaPainel({
  cnpjNormalizado,
  usarExpandNaQuery = false,
  expandirDiagnosticoId = null,
  diagnosticoSemeado = null,
  cabecalhoSlot,
  onDiagnosticosAlterados,
  onListaDetalheAtualizado,
  selecaoComparacaoIds = [],
  onToggleSelecaoComparacao,
}: EmpresaDiagnosticosListaPainelProps) {
  const comSelecao = Boolean(onToggleSelecaoComparacao);
  const gridCols = comSelecao ? GRID_COLS_EMPRESA_COM_SELECAO : GRID_COLS_EMPRESA;
  const selecaoSet = useMemo(() => new Set(selecaoComparacaoIds), [selecaoComparacaoIds]);
  const router = useRouter();
  const searchParams = useSearchParams();
  const [diagnosticos, setDiagnosticos] = useState<DiagnosticoResumoApi[] | null>(null);
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const [detalhesPorId, setDetalhesPorId] = useState<Record<string, DiagnosticoDetalheApi>>(() =>
    diagnosticoSemeado ? { [diagnosticoSemeado.id]: diagnosticoSemeado } : {},
  );
  const [linhaAbertaId, setLinhaAbertaId] = useState<string | null>(null);
  const [detalheCarregandoId, setDetalheCarregandoId] = useState<string | null>(null);
  /** Diálogo «Mudar estado» — só um por grelha (abre com o id do diagnóstico alvo). */
  const [painelEstadoDialogDiagId, setPainelEstadoDialogDiagId] = useState<string | null>(null);
  const [painelEstadoDraft, setPainelEstadoDraft] = useState<PainelEstadoCicloApi | null>(null);
  const [painelEstadoSaving, setPainelEstadoSaving] = useState(false);
  const [painelEstadoErr, setPainelEstadoErr] = useState<string | null>(null);
  const [hashLocal, setHashLocal] = useState("");
  /** Menu «Ações» — portal em `document.body` (Card shadcn usa `overflow-hidden`). */
  const [acoesMenuDiagId, setAcoesMenuDiagId] = useState<string | null>(null);
  const [menuAnchorRect, setMenuAnchorRect] = useState<DOMRect | null>(null);
  const [pdfQuestionarioCarregando, setPdfQuestionarioCarregando] = useState(false);
  const onDiagnosticosAlteradosRef = useRef(onDiagnosticosAlterados);
  const onListaDetalheAtualizadoRef = useRef(onListaDetalheAtualizado);

  useEffect(() => {
    onDiagnosticosAlteradosRef.current = onDiagnosticosAlterados;
  }, [onDiagnosticosAlterados]);

  useEffect(() => {
    onListaDetalheAtualizadoRef.current = onListaDetalheAtualizado;
  }, [onListaDetalheAtualizado]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const ler = () => setHashLocal(window.location.hash.replace(/^#/, "").trim());
    ler();
    window.addEventListener("hashchange", ler);
    return () => window.removeEventListener("hashchange", ler);
  }, []);

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

  /** Ficha ou empresa: expande só com âncora (#) apontando para secção dentro do painel expandido. */
  useEffect(() => {
    if (!hashLocal || !HASHES_QUE_ABREM_LINHA.has(hashLocal)) return;
    const sid = expandirDiagnosticoId?.trim();
    if (!sid || !diagnosticos?.some((d) => d.id === sid)) return;
    setLinhaAbertaId(sid);
  }, [hashLocal, expandirDiagnosticoId, diagnosticos]);

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
        const rows = await fetchDiagnosticosResumoTodasPaginasPorEmpresa(cnpjNormalizado);
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

  /** Detalhe sob demanda ao expandir linha (evita N× GET pesado no load da página empresa). */
  useEffect(() => {
    if (!linhaAbertaId || !temSessaoPainelParaApiCliente()) return;
    if (detalhesPorId[linhaAbertaId]) return;

    let cancel = false;
    setDetalheCarregandoId(linhaAbertaId);
    void fetchDiagnosticoDetalhe(linhaAbertaId)
      .then((d) => {
        if (!cancel) {
          setDetalhesPorId((prev) => ({ ...prev, [d.id]: d }));
          startTransition(() => {
            onListaDetalheAtualizadoRef.current?.(d);
          });
        }
      })
      .catch(() => {
        if (!cancel) setErro("Não foi possível carregar o detalhe deste ciclo. Tente novamente.");
      })
      .finally(() => {
        if (!cancel) setDetalheCarregandoId(null);
      });

    return () => {
      cancel = true;
    };
  }, [linhaAbertaId, detalhesPorId]);

  const fecharMenuAcoes = useCallback(() => {
    setAcoesMenuDiagId(null);
    setMenuAnchorRect(null);
  }, []);

  const toggleMenuAcoes = useCallback(
    (ev: React.MouseEvent<HTMLButtonElement>, diagId: string) => {
      ev.stopPropagation();
      if (acoesMenuDiagId === diagId) {
        fecharMenuAcoes();
        return;
      }
      setMenuAnchorRect(ev.currentTarget.getBoundingClientRect());
      setAcoesMenuDiagId(diagId);
    },
    [acoesMenuDiagId, fecharMenuAcoes],
  );

  useEffect(() => {
    if (!acoesMenuDiagId) return;
    const fechar = (ev: MouseEvent) => {
      const alvo = ev.target;
      if (!(alvo instanceof Node)) return;
      const btnRoot = document.querySelector(`[data-acao-menu="${acoesMenuDiagId}"]`);
      const portalRoot = document.querySelector(
        `[data-acao-menu-portal="${acoesMenuDiagId}"]`,
      );
      if (btnRoot?.contains(alvo) || portalRoot?.contains(alvo)) return;
      fecharMenuAcoes();
    };
    const onKey = (ev: KeyboardEvent) => {
      if (ev.key === "Escape") fecharMenuAcoes();
    };
    const timer = window.setTimeout(() => {
      document.addEventListener("click", fechar);
      document.addEventListener("keydown", onKey);
    }, 0);
    return () => {
      window.clearTimeout(timer);
      document.removeEventListener("click", fechar);
      document.removeEventListener("keydown", onKey);
    };
  }, [acoesMenuDiagId, fecharMenuAcoes]);

  useLayoutEffect(() => {
    if (!acoesMenuDiagId) return;
    const reposicionar = () => {
      const btn = document.querySelector<HTMLButtonElement>(
        `[data-acao-menu="${acoesMenuDiagId}"] button`,
      );
      if (btn) setMenuAnchorRect(btn.getBoundingClientRect());
    };
    const fecharScroll = () => fecharMenuAcoes();
    window.addEventListener("resize", reposicionar);
    window.addEventListener("scroll", fecharScroll, true);
    return () => {
      window.removeEventListener("resize", reposicionar);
      window.removeEventListener("scroll", fecharScroll, true);
    };
  }, [acoesMenuDiagId, fecharMenuAcoes]);

  useEffect(() => {
    if (!painelEstadoDialogDiagId || !temSessaoPainelParaApiCliente()) return;
    if (detalhesPorId[painelEstadoDialogDiagId]?.versao_otimista != null) return;
    let cancel = false;
    void fetchDiagnosticoDetalhe(painelEstadoDialogDiagId)
      .then((d) => {
        if (!cancel) setDetalhesPorId((p) => ({ ...p, [d.id]: d }));
      })
      .catch(() => {
        if (!cancel) setPainelEstadoErr("Não foi possível preparar a alteração de estado agora.");
      });
    return () => {
      cancel = true;
    };
  }, [painelEstadoDialogDiagId, detalhesPorId]);

  useEffect(() => {
    if (diagnosticos === null) return;
    const rows = diagnosticos;
    startTransition(() => {
      onDiagnosticosAlteradosRef.current?.(rows);
    });
  }, [diagnosticos]);

  const aoAtualizarDetalhe = useCallback((d: DiagnosticoDetalheApi) => {
    setDetalhesPorId((prev) => ({ ...prev, [d.id]: d }));
    startTransition(() => {
      onListaDetalheAtualizadoRef.current?.(d);
    });
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

  const aplicarMudancaPainelEstado = useCallback(async () => {
    if (!painelEstadoDialogDiagId || painelEstadoDraft == null) return;
    const versaoPatch =
      detalhesPorId[painelEstadoDialogDiagId]?.versao_otimista ??
      diagnosticos?.find((row) => row.id === painelEstadoDialogDiagId)?.versao_otimista ??
      null;
    if (versaoPatch == null) {
      setPainelEstadoErr(
        "Versão otimista indisponível — aguarde a sincronização ou expanda a linha para carregar o detalhe.",
      );
      return;
    }
    setPainelEstadoSaving(true);
    setPainelEstadoErr(null);
    try {
      const json = await patchPainelEstadoCicloDiagnostico({
        diagnosticoId: painelEstadoDialogDiagId,
        painel_estado_ciclo: painelEstadoDraft,
        versao_esperada: versaoPatch,
      });
      setDiagnosticos((prev) =>
        (prev ?? []).map((row) =>
          row.id === painelEstadoDialogDiagId
            ? {
                ...row,
                painel_estado_ciclo: json.painel_estado_ciclo ?? painelEstadoDraft,
                versao_otimista: json.versao_otimista ?? row.versao_otimista,
              }
            : row,
        ),
      );
      setDetalhesPorId((prev) => ({ ...prev, [json.id]: json }));
      startTransition(() => {
        onListaDetalheAtualizadoRef.current?.(json);
      });
      setPainelEstadoDialogDiagId(null);
    } catch (e) {
      setPainelEstadoErr(e instanceof Error ? e.message : "Falha ao gravar estado.");
    } finally {
      setPainelEstadoSaving(false);
    }
  }, [
    painelEstadoDialogDiagId,
    painelEstadoDraft,
    detalhesPorId,
    diagnosticos,
  ]);

  const linhasGrelha = useMemo(() => {
    if (diagnosticos === null) return [];
    const base = diagnosticos;
    if (!diagnosticoSemeado) return base;
    if (base.some((row) => row.id === diagnosticoSemeado.id)) return base;
    /** Inclui o diagnóstico em vista (ex.: finalizado) quando a lista por CNPJ não o devolve. */
    return [resumoApiDesdeDetalheSemeado(diagnosticoSemeado), ...base];
  }, [diagnosticos, diagnosticoSemeado]);

  const semSessao = !temSessaoPainelParaApiCliente();

  const diagMenuAberto = useMemo(
    () => linhasGrelha.find((d) => d.id === acoesMenuDiagId) ?? null,
    [linhasGrelha, acoesMenuDiagId],
  );

  const menuAcoesPortal =
    typeof document !== "undefined" &&
    acoesMenuDiagId &&
    menuAnchorRect &&
    diagMenuAberto
      ? (() => {
          const diag = diagMenuAberto;
          const detailHref = `/dashboard/diagnosticos/${diag.id}`;
          const detalhePrefetch = detalhesPorId[diag.id];
          const pdfHref = hrefRelatorioPdfAbsoluto(
            detalhePrefetch?.relatorio_pdf_url ?? diag.relatorio_pdf_url ?? null,
          );
          const cicloAtual =
            diag.painel_estado_ciclo ?? detalhePrefetch?.painel_estado_ciclo ?? undefined;
          return createPortal(
            <div
              role="menu"
              data-acao-menu-portal={diag.id}
              className="fixed z-[200] min-w-[14rem] max-h-[min(70vh,24rem)] overflow-y-auto rounded-md border bg-popover py-1 text-sm text-popover-foreground shadow-lg"
              style={{
                top: menuAnchorRect.bottom + 4,
                left: menuAnchorRect.right,
                transform: "translateX(-100%)",
              }}
              onMouseDown={(e) => e.stopPropagation()}
            >
              {pdfHref ? (
                <a
                  href={pdfHref}
                  target="_blank"
                  rel="noopener noreferrer"
                  role="menuitem"
                  className="block px-3 py-2 hover:bg-muted/60"
                  onClick={fecharMenuAcoes}
                >
                  Relatório PDF
                </a>
              ) : (
                <span className="block px-3 py-2 text-muted-foreground">PDF indisponível</span>
              )}
              <button
                type="button"
                role="menuitem"
                className="w-full text-left px-3 py-2 hover:bg-muted/60 disabled:opacity-50"
                disabled={pdfQuestionarioCarregando}
                onClick={() => {
                  fecharMenuAcoes();
                  setPdfQuestionarioCarregando(true);
                  void abrirPdfQuestionarioDiagnostico(diag.id)
                    .catch((e) => {
                      window.alert(
                        e instanceof Error ? e.message : "Não foi possível gerar o PDF do questionário.",
                      );
                    })
                    .finally(() => setPdfQuestionarioCarregando(false));
                }}
              >
                Questionário (PDF)
              </button>
              <Link
                href={hrefPrivacidadePainel({ diagnosticoId: diag.id, secao: "retificacoes" })}
                role="menuitem"
                className="block px-3 py-2 hover:bg-muted/60"
                onClick={fecharMenuAcoes}
              >
                Retificações
              </Link>
              <Link
                href={hrefPrivacidadePainel({ diagnosticoId: diag.id, secao: "lgpd" })}
                role="menuitem"
                className="block px-3 py-2 hover:bg-muted/60"
                onClick={fecharMenuAcoes}
              >
                LGPD
              </Link>
              <Link
                href={`${detailHref}#diag-explicacao-score-llm`}
                role="menuitem"
                className="block px-3 py-2 hover:bg-muted/60"
                onClick={fecharMenuAcoes}
              >
                Explicação IA (score)
              </Link>
              <Link
                href={detailHref}
                role="menuitem"
                className="block px-3 py-2 hover:bg-muted/60"
                onClick={fecharMenuAcoes}
              >
                Abrir ficha do diagnóstico
              </Link>
              {diag.plano === "avancado" ? (
                <button
                  type="button"
                  role="menuitem"
                  className="w-full text-left px-3 py-2 hover:bg-muted/60 flex items-center gap-2"
                  onClick={() => {
                    fecharMenuAcoes();
                    aoRefazerDiagnostico(diag.empresa_razao_social);
                  }}
                >
                  <RefreshCw className="h-3.5 w-3.5 shrink-0" aria-hidden />
                  Novo ciclo de diagnóstico
                </button>
              ) : null}
              <button
                type="button"
                role="menuitem"
                className="w-full text-left px-3 py-2 hover:bg-muted/60 border-t mt-1 pt-2"
                onClick={() => {
                  fecharMenuAcoes();
                  setPainelEstadoErr(null);
                  setPainelEstadoDraft((cicloAtual as PainelEstadoCicloApi) ?? "realizado");
                  setPainelEstadoDialogDiagId(diag.id);
                }}
              >
                Mudar estado…
              </button>
            </div>,
            document.body,
          );
        })()
      : null;

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

      {!semSessao && carregando && (
        <p className="text-muted-foreground text-sm" aria-live="polite">
          Carregando diagnósticos desta empresa…
        </p>
      )}

      {!semSessao && !erro && !carregando && diagnosticos !== null && linhasGrelha.length === 0 && (
        <p className="text-muted-foreground text-sm max-w-2xl leading-relaxed">
          Nenhum diagnóstico encontrado para este CNPJ neste painel (ou os registros ainda não incluem{" "}
          <span className="font-mono tabular-nums">{cnpjNormalizado}</span>).
        </p>
      )}

      {!semSessao && !carregando && linhasGrelha.length > 0 && (
        <div className="rounded-xl border bg-card/40">
          <div
            className={`hidden sm:grid ${gridCols} sm:gap-3 sm:items-center px-4 py-3 text-xs font-semibold uppercase tracking-wide text-muted-foreground border-b bg-muted/30`}
          >
            {comSelecao ? (
              <span className="sr-only">Comparar</span>
            ) : null}
            <span>Empresa / ciclo</span>
            <span className="text-center">Score</span>
            <span className="text-center">Ciclo</span>
            <span className="text-center">Data</span>
            <span className="text-center">Ações</span>
          </div>
          <ul className="divide-y" aria-label="Diagnósticos desta empresa no painel">
            {linhasGrelha.map((diag) => {
              const score = diag.score_geral;
              const pct = score != null ? Math.min(100, Math.max(0, score)) : null;
              const quando = new Date(diag.finalizado_em ?? diag.criado_em).toLocaleDateString("pt-BR", {
                day: "2-digit",
                month: "2-digit",
                year: "numeric",
              });
              const aberto = linhaAbertaId === diag.id;
              const detailHref = `/dashboard/diagnosticos/${diag.id}`;
              const detalhePrefetch = detalhesPorId[diag.id];
              const cicloAtual =
                diag.painel_estado_ciclo ?? detalhePrefetch?.painel_estado_ciclo ?? undefined;

              const menuAcoesAberto = acoesMenuDiagId === diag.id;

              return (
                <li key={diag.id} className={menuAcoesAberto ? "relative z-20" : "relative z-0"}>
                  <div
                    className={`px-3 py-4 sm:px-4 space-y-3 sm:space-y-0 sm:grid ${gridCols} sm:gap-3 sm:items-center`}
                  >
                    {comSelecao ? (
                      <div className="flex items-center justify-center sm:justify-start">
                        <input
                          type="checkbox"
                          className="h-4 w-4 rounded border-input"
                          aria-label={`Selecionar para comparar ${diag.empresa_razao_social}`}
                          checked={selecaoSet.has(diag.id)}
                          disabled={
                            !selecaoSet.has(diag.id) &&
                            selecaoSet.size >= MAX_DIAGNOSTICOS_COMPARACAO
                          }
                          onChange={(e) =>
                            onToggleSelecaoComparacao?.(diag.id, e.target.checked)
                          }
                        />
                      </div>
                    ) : null}
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
                    <div className="flex flex-col items-stretch gap-1 sm:flex sm:justify-center sm:items-center">
                      <span className="text-xs text-muted-foreground sm:hidden">Ciclo</span>
                      <Badge variant="outline" className="font-normal w-fit mx-auto sm:mx-0">
                        {rotuloPainelEstadoCiclo(cicloAtual)}
                      </Badge>
                      <span className="text-[10px] leading-tight text-muted-foreground text-center sm:text-center">
                        Evidência: {diag.status === "finalizado" ? "Finalizado" : diag.status}
                      </span>
                    </div>
                    <div className="flex items-center justify-between gap-2 sm:block sm:text-center text-sm text-muted-foreground">
                      <span className="text-xs sm:hidden">Data</span>
                      <span>{quando}</span>
                    </div>
                    <div className="flex flex-col gap-1.5 w-full sm:items-end overflow-visible">
                      <div className="flex flex-wrap gap-1.5 w-full justify-end items-center">
                        <div className="relative shrink-0" data-acao-menu={diag.id}>
                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            className="h-8 text-xs px-3"
                            aria-haspopup="menu"
                            aria-expanded={menuAcoesAberto}
                            onClick={(e) => toggleMenuAcoes(e, diag.id)}
                          >
                            Ações ▾
                          </Button>
                        </div>
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
      {menuAcoesPortal}
      <Dialog
        open={painelEstadoDialogDiagId !== null}
        onOpenChange={(next) => {
          if (!next) {
            setPainelEstadoDialogDiagId(null);
            setPainelEstadoErr(null);
          }
        }}
      >
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Mudar estado do ciclo</DialogTitle>
            <DialogDescription>
              Classifica o acompanhamento na tabela (realizado / em andamento / descartado / finalizado). É uma
              informação operacional do painel — não substitui as evidências já preservadas no diagnóstico finalizado.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2 py-2" role="radiogroup" aria-label="Novo estado do ciclo administrativo">
            {PAINEL_ESTADO_CICLO_VALORES.map((v) => (
              <label
                key={v}
                className={`flex cursor-pointer items-start gap-3 rounded-md border px-3 py-2 text-sm transition-colors ${
                  painelEstadoDraft === v ? "border-primary bg-primary/5" : "border-border hover:bg-muted/40"
                }`}
              >
                <input
                  type="radio"
                  name="painel-estado-ciclo-grid"
                  className="mt-1"
                  checked={painelEstadoDraft === v}
                  onChange={() => setPainelEstadoDraft(v)}
                />
                <span>{rotuloPainelEstadoCiclo(v)}</span>
              </label>
            ))}
          </div>
          {painelEstadoErr ? (
            <p className="text-sm text-destructive" role="alert">
              {painelEstadoErr}
            </p>
          ) : null}
          <DialogFooter className="gap-2 sm:gap-0">
            <Button type="button" variant="outline" onClick={() => setPainelEstadoDialogDiagId(null)}>
              Cancelar
            </Button>
            <Button
              type="button"
              disabled={painelEstadoSaving || painelEstadoDraft == null}
              onClick={() => void aplicarMudancaPainelEstado()}
            >
              {painelEstadoSaving ? "Gravando…" : "Gravar"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
