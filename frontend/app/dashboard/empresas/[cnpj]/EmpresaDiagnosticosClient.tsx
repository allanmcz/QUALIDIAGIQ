"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { ChevronDown } from "lucide-react";

import EmpresaDiagnosticoExpandedPanel from "@/components/painel/empresa/EmpresaDiagnosticoExpandedPanel";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { fetchDiagnosticoDetalhe } from "@/lib/api/fetch_diagnostico_detalhe";
import {
  fetchDiagnosticosResumoTodasPaginasPorEmpresa,
  type DiagnosticoResumoApi,
} from "@/lib/api/lista_diagnosticos";
import { temSessaoPainelParaApiCliente } from "@/lib/api/config";
import { buildWizardUrlNovaDiagnosticoEmpresa } from "@/lib/dashboard/empresa_diagnostico_urls";
import type { DiagnosticoDetalheApi } from "@/types/diagnostico_detalhe";

function mascaraCnpj14(d: string): string {
  const c = d.replace(/\D/g, "");
  if (c.length !== 14) return d;
  return c.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/, "$1.$2.$3/$4-$5");
}

/** Diagnóstico mais recente (finalizado ou criado) — atalho «plano empresa». */
function pickLatestDiagnosticId(rows: DiagnosticoResumoApi[]): string | null {
  if (!rows.length) return null;
  const sorted = [...rows].sort((a, b) => {
    const da = new Date(a.finalizado_em ?? a.criado_em).getTime();
    const db = new Date(b.finalizado_em ?? b.criado_em).getTime();
    return db - da;
  });
  return sorted[0]?.id ?? null;
}

const PREFETCH_CONCORRENCIA = 4;

export default function EmpresaDiagnosticosClient({
  cnpjNormalizado,
  razaoSocialHint,
}: {
  cnpjNormalizado: string;
  razaoSocialHint: string;
}) {
  const [diagnosticos, setDiagnosticos] = useState<DiagnosticoResumoApi[] | null>(null);
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  /** Cache GET /diagnosticos/{id} para ranking global + evitar novo GET ao expandir. */
  const [detalhesPorId, setDetalhesPorId] = useState<Record<string, DiagnosticoDetalheApi>>({});
  const [prefetchErro, setPrefetchErro] = useState<string | null>(null);
  const [linhaAbertaId, setLinhaAbertaId] = useState<string | null>(null);

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

  /** Prefetch em segundo plano — alimenta ranking «global empresa» e cache por ID. */
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

  const detalhesListaAgregacao = useMemo(() => Object.values(detalhesPorId), [detalhesPorId]);

  const tituloEmpresa = useMemo(() => {
    const hint = razaoSocialHint.trim();
    if (hint.length >= 3) return hint;
    const primeiro = diagnosticos?.[0]?.empresa_razao_social?.trim();
    if (primeiro && primeiro.length >= 3) return primeiro;
    return `Empresa · CNPJ ${mascaraCnpj14(cnpjNormalizado)}`;
  }, [razaoSocialHint, diagnosticos, cnpjNormalizado]);

  const latestId = useMemo(
    () => (diagnosticos?.length ? pickLatestDiagnosticId(diagnosticos) : null),
    [diagnosticos],
  );

  const hrefPlanoEmpresa =
    latestId != null
      ? `/dashboard/diagnosticos/${latestId}#m06-cronograma-tabela-heading`
      : null;

  const aoAtualizarDetalhe = useCallback((d: DiagnosticoDetalheApi) => {
    setDetalhesPorId((prev) => ({ ...prev, [d.id]: d }));
  }, []);

  const daEmpresa = diagnosticos ?? [];
  const semSessao = !temSessaoPainelParaApiCliente();

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
              {carregando ? " · …" : ` · ${daEmpresa.length} diagnóstico(s) neste tenant`}
            </p>
          </div>
          {!semSessao && (
            <div className="flex flex-col gap-2 sm:items-end">
              <Button asChild className="shrink-0 w-full sm:w-auto">
                <Link href={buildWizardUrlNovaDiagnosticoEmpresa(cnpjNormalizado, tituloEmpresa)}>
                  Novo diagnóstico (esta empresa)
                </Link>
              </Button>
              <div className="flex flex-col xs:flex-row gap-2 w-full sm:w-auto">
                {hrefPlanoEmpresa ? (
                  <Button variant="secondary" size="sm" className="w-full sm:w-auto" asChild>
                    <Link href={hrefPlanoEmpresa}>Plano de ação (empresa)</Link>
                  </Button>
                ) : null}
                <Button variant="outline" size="sm" className="w-full sm:w-auto" asChild>
                  <Link href="/dashboard/privacidade">LGPD e direitos do titular</Link>
                </Button>
              </div>
              <p className="text-xs text-muted-foreground max-w-md sm:text-right">
                Plano e cronograma consolidados abrem no diagnóstico mais recente. LGPD: área do tenant (solicitações,
                portabilidade).
              </p>
            </div>
          )}
        </div>

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
              A consolidar ranking global… ({Object.keys(detalhesPorId).length}/{daEmpresa.length} diagnósticos com
              detalhe carregado)
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
            <span className="font-mono tabular-nums">{cnpjNormalizado}</span>). Pode iniciar um novo ciclo com o botão
            acima.
          </p>
        )}

        {!semSessao && !carregando && daEmpresa.length > 0 && (
          <div className="rounded-xl border bg-card/40 overflow-hidden">
            <div className="hidden md:grid md:grid-cols-[1fr_auto_auto_auto_auto] md:gap-3 md:items-center px-4 py-3 text-xs font-semibold uppercase tracking-wide text-muted-foreground border-b bg-muted/30">
              <span>Empresa / ciclo</span>
              <span className="text-center">Score</span>
              <span className="text-center">Estado</span>
              <span className="text-center">Data</span>
              <span className="sr-only">Expandir</span>
            </div>
            <ul className="divide-y">
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
                    <div className="flex flex-col md:grid md:grid-cols-[1fr_auto_auto_auto_auto] md:gap-3 md:items-center px-3 py-4 sm:px-4">
                      <div className="min-w-0 mb-2 md:mb-0">
                        <Link
                          href={detailHref}
                          className="font-medium text-foreground hover:text-primary hover:underline line-clamp-2"
                        >
                          {diag.empresa_razao_social}
                        </Link>
                        <p className="text-xs text-muted-foreground font-mono mt-0.5 truncate">
                          ID {diag.id}
                        </p>
                      </div>
                      <div className="flex flex-wrap items-center gap-3 md:contents">
                        <div className="tabular-nums text-sm md:text-center md:min-w-[4rem]">
                          {pct != null ? `${pct.toFixed(1)}` : "—"}
                        </div>
                        <div className="md:flex md:justify-center">
                          <Badge variant={diag.plano === "avancado" ? "default" : "secondary"}>
                            {diag.status === "finalizado" ? "Finalizado" : diag.status}
                          </Badge>
                        </div>
                        <div className="text-sm text-muted-foreground md:text-center md:min-w-[5.5rem]">
                          {quando}
                        </div>
                        <div className="md:flex md:justify-end">
                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            className="gap-1.5 w-full md:w-auto mt-2 md:mt-0"
                            aria-expanded={aberto}
                            onClick={() => setLinhaAbertaId((id) => (id === diag.id ? null : diag.id))}
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
                      <EmpresaDiagnosticoExpandedPanel
                        diagnosticoId={diag.id}
                        detalhePrecarregado={detalhesPorId[diag.id] ?? null}
                        detalhesEmpresaParaAgregado={detalhesListaAgregacao}
                        onDetalheAtualizado={aoAtualizarDetalhe}
                      />
                    ) : null}
                  </li>
                );
              })}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
