"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  Bar,
  BarChart,
  Cell,
  PolarAngleAxis,
  PolarGrid,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Pencil } from "lucide-react";

import { ExplicacaoScoreLlmCard } from "@/components/painel/ExplicacaoScoreLlmCard";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
  cabecalhosAuthPainelOpcional,
  getApiUrlForFetch,
  temSessaoPainelParaApiCliente,
} from "@/lib/api/config";
import { encerrarSessaoPainelSe401 } from "@/lib/auth/painel_session";
import {
  BAR_GAP_COLORS,
  aggregateRankingGapsEmpresa,
  corHeat,
  radarRowsFromScore,
  rankingGapsFromScore,
  type RankingGapRow,
} from "@/lib/painel/diagnostico_scores";
import {
  M12_NUM_ITENS,
  m12EstadoInicialVazio,
  m12ValoresSeCompleto,
  normalizarM12DoApi,
  rotuloLikertM12,
} from "@/lib/painel/m12_autoconf_utils";
import type { DiagnosticoDetalheApi } from "@/types/diagnostico_detalhe";

type Props = {
  diagnosticoId: string;
  /** Se já veio do prefetch (lista completa), evita GET duplicado ao expandir. */
  detalhePrecarregado: DiagnosticoDetalheApi | null;
  /** Todos os detalhes com score — para bloco «global empresa». */
  detalhesEmpresaParaAgregado: DiagnosticoDetalheApi[];
  onDetalheAtualizado?: (d: DiagnosticoDetalheApi) => void;
};

export default function EmpresaDiagnosticoExpandedPanel({
  diagnosticoId,
  detalhePrecarregado,
  detalhesEmpresaParaAgregado,
  onDetalheAtualizado,
}: Props) {
  const [data, setData] = useState<DiagnosticoDetalheApi | null>(detalhePrecarregado);
  const [loading, setLoading] = useState(!detalhePrecarregado);
  const [loadErr, setLoadErr] = useState<string | null>(null);
  const versaoOtimistaRef = useRef<number | null>(null);

  const [m12Likert, setM12Likert] = useState<(number | null)[]>([]);
  const [m12ModalIndex, setM12ModalIndex] = useState<number | null>(null);
  const [m12ModalDraft, setM12ModalDraft] = useState<number | null>(null);
  const [m12Saving, setM12Saving] = useState(false);
  const [m12Msg, setM12Msg] = useState<string | null>(null);

  useEffect(() => {
    if (detalhePrecarregado) {
      setData(detalhePrecarregado);
      setLoading(false);
      setLoadErr(null);
      if (detalhePrecarregado.versao_otimista != null) {
        versaoOtimistaRef.current = detalhePrecarregado.versao_otimista;
      }
      return;
    }
    let cancel = false;
    (async () => {
      setLoading(true);
      setLoadErr(null);
      try {
        const json = await fetchDiagnosticoDetalhe(diagnosticoId);
        if (cancel) return;
        setData(json);
        if (json.versao_otimista != null) versaoOtimistaRef.current = json.versao_otimista;
      } catch (e) {
        if (!cancel) setLoadErr(e instanceof Error ? e.message : "Falha ao carregar detalhe.");
      } finally {
        if (!cancel) setLoading(false);
      }
    })();
    return () => {
      cancel = true;
    };
  }, [diagnosticoId, detalhePrecarregado]);

  useEffect(() => {
    if (data?.versao_otimista != null) versaoOtimistaRef.current = data.versao_otimista;
  }, [data?.versao_otimista]);

  const frenteAbnt10 = useMemo(() => {
    return (
      data?.checklist?.find((f) => f.nome.includes("17301") && f.nome.includes("10")) ?? null
    );
  }, [data?.checklist]);

  useEffect(() => {
    if (!frenteAbnt10 || frenteAbnt10.acoes.length !== M12_NUM_ITENS) return;
    const parsed = normalizarM12DoApi(data?.checklist_m12_autoconf ?? null);
    setM12Likert(parsed ? [...parsed] : m12EstadoInicialVazio());
    setM12Msg(null);
  }, [data?.checklist_m12_autoconf, data?.id, frenteAbnt10]);

  const radarData = useMemo(() => radarRowsFromScore(data?.score ?? null), [data?.score]);
  const rankingEsteDiag = useMemo(() => rankingGapsFromScore(data?.score ?? null), [data?.score]);

  const rankingGlobalEmpresa = useMemo((): RankingGapRow[] => {
    return aggregateRankingGapsEmpresa(detalhesEmpresaParaAgregado.map((d) => ({ score: d.score })));
  }, [detalhesEmpresaParaAgregado]);

  const refetchDetalhe = useCallback(async () => {
    const base = getApiUrlForFetch().replace(/\/$/, "");
    const res = await fetch(`${base}/diagnosticos/${diagnosticoId}`, {
      headers: {
        Accept: "application/json",
        ...cabecalhosAuthPainelOpcional(),
      },
      cache: "no-store",
      credentials: "include",
    });
    if (!res.ok) return;
    const json = (await res.json()) as DiagnosticoDetalheApi;
    if (json.versao_otimista != null) versaoOtimistaRef.current = json.versao_otimista;
    setData(json);
    onDetalheAtualizado?.(json);
  }, [diagnosticoId, onDetalheAtualizado]);

  const salvarM12LikertCompleto = useCallback(
    async (proximo: number[]): Promise<boolean> => {
      const autenticado = temSessaoPainelParaApiCliente();
      if (!autenticado || data?.status !== "finalizado") {
        setM12Msg("É necessário estar autenticado e o diagnóstico finalizado.");
        return false;
      }
      const v = versaoOtimistaRef.current;
      if (v == null) {
        setM12Msg("Versão otimista indisponível — recarregue a página.");
        return false;
      }
      setM12Saving(true);
      setM12Msg(null);
      const base = getApiUrlForFetch().replace(/\/$/, "");
      try {
        const res = await fetch(`${base}/diagnosticos/${diagnosticoId}/checklist-m12-autoconf`, {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
            Accept: "application/json",
            ...cabecalhosAuthPainelOpcional(),
            "If-Match": String(v),
          },
          credentials: "include",
          body: JSON.stringify({ checklist_m12_autoconf: proximo }),
        });
        if (encerrarSessaoPainelSe401(res.status)) return false;
        if (res.ok) {
          const json = (await res.json()) as DiagnosticoDetalheApi;
          if (json.versao_otimista != null) versaoOtimistaRef.current = json.versao_otimista;
          const sync = normalizarM12DoApi(json.checklist_m12_autoconf);
          setM12Likert(sync ? [...sync] : [...proximo]);
          setData(json);
          setM12Msg("Autoconf M12 gravada.");
          onDetalheAtualizado?.(json);
          return true;
        }
        if (res.status === 412) {
          setM12Msg("Conflito de versão — a atualizar dados…");
          await refetchDetalhe();
          return false;
        }
        const t = await res.text();
        setM12Msg(`Não foi possível gravar (${res.status}): ${t.slice(0, 160)}`);
        return false;
      } catch {
        setM12Msg("Falha de rede ao gravar o M12.");
        return false;
      } finally {
        setM12Saving(false);
      }
    },
    [data?.status, diagnosticoId, onDetalheAtualizado, refetchDetalhe],
  );

  const gravarM12NaApi = useCallback(async () => {
    const payload = m12ValoresSeCompleto(m12Likert);
    if (!payload) {
      setM12Msg("Assine os 10 controles (nível 1 a 5 em cada um) antes de gravar na API.");
      return;
    }
    await salvarM12LikertCompleto(payload);
  }, [m12Likert, salvarM12LikertCompleto]);

  const confirmarM12Modal = useCallback(() => {
    const idx = m12ModalIndex;
    if (idx === null || idx < 0 || idx >= M12_NUM_ITENS || m12ModalDraft === null) return;
    setM12Likert((prev) => {
      const base = prev.length === M12_NUM_ITENS ? [...prev] : m12EstadoInicialVazio();
      base[idx] = m12ModalDraft;
      return base;
    });
    setM12ModalIndex(null);
  }, [m12ModalIndex, m12ModalDraft]);

  const m12ProgressoAssinalados = m12Likert.filter((x) => x !== null).length;
  const m12CompletoParaApi = m12ValoresSeCompleto(m12Likert) !== null;

  const pdfHref = hrefRelatorioPdfAbsoluto(data?.relatorio_pdf_url ?? null);
  const fichaCompletaHref = `/dashboard/diagnosticos/${diagnosticoId}`;

  if (loading) {
    return (
      <div className="rounded-lg border bg-muted/20 px-4 py-6 text-sm text-muted-foreground">
        A carregar detalhes do diagnóstico…
      </div>
    );
  }

  if (loadErr || !data) {
    return (
      <div className="rounded-lg border border-destructive/40 bg-destructive/10 px-4 py-3 text-sm text-destructive">
        {loadErr ?? "Sem dados."}
      </div>
    );
  }

  return (
    <div className="rounded-xl border bg-card/50 p-4 sm:p-6 space-y-8 mt-4 motion-reduce:transition-none">
      <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center sm:justify-between">
        <div className="flex flex-wrap gap-2">
          {pdfHref ? (
            <Button variant="default" size="sm" asChild>
              <a href={pdfHref} target="_blank" rel="noopener noreferrer">
                Relatório PDF (este diagnóstico)
              </a>
            </Button>
          ) : (
            <Badge variant="secondary">PDF ainda não disponível</Badge>
          )}
          <Button variant="outline" size="sm" asChild>
            <Link href={`${fichaCompletaHref}#diag-retificacoes`}>Retificações (este diagnóstico)</Link>
          </Button>
          <Button variant="outline" size="sm" asChild>
            <Link href={`${fichaCompletaHref}#diag-privacidade-lgpd`}>LGPD deste diagnóstico</Link>
          </Button>
          <Button variant="outline" size="sm" asChild>
            <Link href={`${fichaCompletaHref}#diag-explicacao-score-llm`}>
              Explicação IA (este diagnóstico)
            </Link>
          </Button>
          <Button variant="outline" size="sm" asChild>
            <Link href={fichaCompletaHref}>Ficha completa do diagnóstico</Link>
          </Button>
        </div>
      </div>

      {rankingGlobalEmpresa.length > 0 && (
        <section
          aria-labelledby="empresa-ranking-global-heading"
          className="rounded-xl border bg-muted/15 px-4 py-5 sm:px-6"
        >
          <h3 id="empresa-ranking-global-heading" className="text-base font-semibold tracking-tight mb-2">
            Ranking de gaps — visão global da empresa (média dos diagnósticos deste CNPJ)
          </h3>
          <p className="text-sm text-muted-foreground mb-4">
            Ordem: menor média de score por dimensão primeiro — agrega todos os diagnósticos carregados para esta PJ no
            tenant.
          </p>
          <ol className="list-decimal list-inside space-y-1.5 text-sm">
            {rankingGlobalEmpresa.map((row, idx) => (
              <li key={row.dimensao}>
                <span className="capitalize font-medium">{row.dimensao}</span>
                <span className="text-muted-foreground"> — média </span>
                <span className="tabular-nums font-semibold">{row.valor.toFixed(1)}</span>
                <span className="text-muted-foreground"> / 100</span>
                {idx === 0 ? <span className="sr-only"> (prioridade média máxima)</span> : null}
              </li>
            ))}
          </ol>
        </section>
      )}

      {rankingEsteDiag.length > 0 && (
        <div className="space-y-6">
          <section
            aria-labelledby="diag-ranking-gaps-heading"
            className="rounded-xl border bg-card px-4 py-5 sm:px-6 shadow-sm"
          >
            <h3 id="diag-ranking-gaps-heading" className="text-base font-semibold tracking-tight mb-4">
              Ranking explícito de gaps — este diagnóstico (M05)
            </h3>
            <p className="text-sm text-muted-foreground mb-4">
              Ordem: menor score por dimensão primeiro — mesmo critério da ficha completa.
            </p>
            <ol className="list-decimal list-inside space-y-2 text-sm sm:text-base">
              {rankingEsteDiag.map((row, idx) => (
                <li key={row.dimensao} className="marker:font-semibold">
                  <span className="capitalize font-medium text-foreground">{row.dimensao}</span>
                  <span className="text-muted-foreground"> — score </span>
                  <span className="tabular-nums font-semibold text-foreground">{row.valor.toFixed(1)}</span>
                  <span className="text-muted-foreground"> / 100</span>
                  {idx === 0 ? (
                    <span className="sr-only"> (prioridade máxima — maior gap)</span>
                  ) : null}
                </li>
              ))}
            </ol>
          </section>

          {radarData && radarData.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Radar por dimensão</CardTitle>
              </CardHeader>
              <CardContent className="h-[280px] sm:h-[320px]">
                <ResponsiveContainer width="100%" height="100%">
                  <RadarChart data={radarData} cx="50%" cy="50%" outerRadius="75%">
                    <PolarGrid />
                    <PolarAngleAxis dataKey="dimensao" tick={{ fontSize: 10 }} />
                    <Radar name="Score" dataKey="valor" stroke="#2563eb" fill="#3b82f6" fillOpacity={0.35} />
                  </RadarChart>
                </ResponsiveContainer>
                {data.score?.score_geral && (
                  <p className="text-center text-xs text-muted-foreground mt-2">
                    Score geral: <strong>{data.score.score_geral.valor}</strong> / 100
                  </p>
                )}
              </CardContent>
            </Card>
          )}

          <ExplicacaoScoreLlmCard
            diagnosticoId={diagnosticoId}
            diagnosticoStatus={data.status}
            scoreGeral={data.score?.score_geral?.valor ?? null}
            inicial={data.explicacao_score_llm ?? null}
            className="mb-0 scroll-mt-0"
          />

          <div className="grid md:grid-cols-2 gap-6">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base">Heatmap rápido por dimensão (M05)</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground mb-4">
                  Menor score (vermelho) = maior gap neste diagnóstico.
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {rankingEsteDiag.map((row) => (
                    <div
                      key={row.dimensao}
                      className={`rounded-md px-3 py-2 text-sm text-white flex justify-between ${corHeat(row.valor)}`}
                    >
                      <span className="font-medium capitalize">{row.dimensao}</span>
                      <span>{row.valor.toFixed(0)}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base">Ranking de gaps — barras (este diagnóstico)</CardTitle>
              </CardHeader>
              <CardContent className="h-[260px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={rankingEsteDiag} layout="vertical" margin={{ left: 8, right: 12 }}>
                    <XAxis type="number" domain={[0, 100]} />
                    <YAxis type="category" dataKey="dimensao" width={108} tick={{ fontSize: 10 }} />
                    <Tooltip
                      formatter={(v) => [
                        `${typeof v === "number" ? v.toFixed(1) : String(v ?? "")} / 100`,
                        "Score",
                      ]}
                    />
                    <Bar dataKey="valor" radius={[0, 4, 4, 0]}>
                      {rankingEsteDiag.map((_, i) => (
                        <Cell key={i} fill={BAR_GAP_COLORS[Math.min(i, BAR_GAP_COLORS.length - 1)]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {frenteAbnt10 && frenteAbnt10.acoes.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Autoconferência ABNT — 10 controles (M12)</CardTitle>
            <p className="text-sm font-normal text-muted-foreground">
              Escala Likert 1 a 5; gravar na API com versão otimista (If-Match). Igual à ficha completa.
            </p>
            {data.status === "finalizado" ? (
              <div className="flex flex-col gap-3 mt-4 sm:flex-row sm:flex-wrap sm:items-center sm:justify-between">
                <p className="text-sm font-medium tabular-nums">
                  Progresso: {m12ProgressoAssinalados}/{M12_NUM_ITENS} controles assinalados
                </p>
                <Button
                  type="button"
                  disabled={m12Saving || data.status !== "finalizado" || !m12CompletoParaApi}
                  onClick={() => void gravarM12NaApi()}
                >
                  {m12Saving ? "Gravando…" : "Gravar autoconf na API"}
                </Button>
              </div>
            ) : null}
            {m12Msg ? (
              <p className="text-sm text-muted-foreground mt-2" role="status">
                {m12Msg}
              </p>
            ) : null}
          </CardHeader>
          <CardContent className="space-y-3">
            {frenteAbnt10.acoes.map((a, i) => {
              const valor = m12Likert[i] ?? null;
              return (
                <div
                  key={a.descricao + String(i)}
                  className="flex flex-col gap-3 rounded-lg border bg-muted/10 p-3 sm:flex-row sm:items-start sm:justify-between"
                >
                  <p className="text-sm leading-snug flex-1 min-w-0">{a.descricao}</p>
                  <div className="flex flex-wrap items-center gap-2 shrink-0">
                    <Badge variant="secondary" className="text-xs font-normal max-w-[14rem] sm:max-w-xs text-left">
                      {valor === null || valor === undefined
                        ? "Não assinalado — use Alterar"
                        : `${valor} — ${rotuloLikertM12(valor)}`}
                    </Badge>
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      className="gap-1.5"
                      disabled={m12Saving || data.status !== "finalizado"}
                      onClick={() => {
                        setM12ModalIndex(i);
                        setM12ModalDraft(valor ?? null);
                      }}
                    >
                      <Pencil className="h-3.5 w-3.5 shrink-0" aria-hidden />
                      Alterar
                    </Button>
                  </div>
                </div>
              );
            })}
          </CardContent>
        </Card>
      )}

      <Dialog
        open={m12ModalIndex !== null}
        onOpenChange={(open) => {
          if (!open) {
            setM12ModalIndex(null);
            setM12ModalDraft(null);
          }
        }}
      >
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Controle M12 — escala Likert</DialogTitle>
            <DialogDescription>
              Escolha 1–5; «Aplicar» atualiza só este controlo no ecrã. «Gravar autoconf na API» persiste os 10.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2 py-2" role="radiogroup" aria-label="Escala Likert 1 a 5">
            {([1, 2, 3, 4, 5] as const).map((n) => (
              <label
                key={n}
                className={`flex cursor-pointer items-start gap-3 rounded-md border px-3 py-2 text-sm transition-colors ${
                  m12ModalDraft === n ? "border-primary bg-primary/5" : "border-border hover:bg-muted/40"
                }`}
              >
                <input
                  type="radio"
                  name="m12-likert-empresa"
                  className="mt-0.5"
                  checked={m12ModalDraft === n}
                  onChange={() => setM12ModalDraft(n)}
                />
                <span>
                  <span className="font-semibold text-foreground">{n}</span> — {rotuloLikertM12(n)}
                </span>
              </label>
            ))}
          </div>
          <DialogFooter className="gap-2 sm:gap-0">
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                setM12ModalIndex(null);
                setM12ModalDraft(null);
              }}
            >
              Cancelar
            </Button>
            <Button
              type="button"
              disabled={m12ModalDraft === null || data.status !== "finalizado"}
              onClick={() => confirmarM12Modal()}
            >
              Aplicar ao controle
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
