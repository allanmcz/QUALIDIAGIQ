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

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getAccessToken, getApiUrl } from "@/lib/api/config";

type AcaoChecklist = {
  descricao: string;
  responsavel: string;
  prazo: string;
  criticidade: string;
  base_legal?: string | null;
  prioridade?: number;
};
type FrenteChecklist = { nome: string; acoes: AcaoChecklist[] };

type MatrizLinha = {
  departamento: string;
  impacto_resumo: string;
  criticidade: string;
  base_legal?: string | null;
};

type CronogramaFase = {
  fase: string;
  foco: string;
  referencia_normativa: string;
};

export type DiagnosticoDetalheApi = {
  id: string;
  empresa_razao_social: string;
  plano: string;
  status: string;
  relatorio_pdf_url: string | null;
  checklist: FrenteChecklist[] | null;
  matriz_impacto: MatrizLinha[] | null;
  cronograma: CronogramaFase[] | null;
  checklist_m12_autoconf: boolean[] | null;
  versao_otimista: number | null;
  score: {
    score_geral: { valor: number };
    score_por_dimensao: Record<string, { valor: number; peso_total_aplicado: number }>;
  } | null;
};

function mockDiagnostico(id: string): DiagnosticoDetalheApi {
  const isAvancado = id.startsWith("7");
  return {
    id,
    empresa_razao_social: isAvancado ? "Acme Corp S/A" : "Tech Solutions Ltda",
    plano: isAvancado ? "avancado" : "gratuito",
    status: "finalizado",
    relatorio_pdf_url: null,
    cronograma: [
      {
        fase: "Curto prazo (0-12 meses)",
        foco: "Governança e mapeamento.",
        referencia_normativa: "LC 214/2025",
      },
    ],
    matriz_impacto: [
      {
        departamento: "Fiscal",
        impacto_resumo: "Exemplo: apuração CBS.",
        criticidade: "Crítica",
        base_legal: "LC 214/2025",
      },
    ],
    checklist_m12_autoconf: null,
    versao_otimista: 1,
    score: {
      score_geral: { valor: 62 },
      score_por_dimensao: {
        fiscal: { valor: 55, peso_total_aplicado: 1.5 },
        tecnologica: { valor: 48, peso_total_aplicado: 1.4 },
        compliance_abnt_17301: { valor: 70, peso_total_aplicado: 1.5 },
      },
    },
    checklist: [
      {
        nome: "Governança e Comitê",
        acoes: [
          {
            descricao: "Constituir Comitê Tributário Reforma",
            responsavel: "Diretoria",
            prazo: "Out/2025",
            criticidade: "Crítica",
            prioridade: 10,
            base_legal: "LC 214/2025 art. 5º",
          },
        ],
      },
    ],
  };
}

function corHeat(valor: number): string {
  if (valor < 40) return "bg-red-500/85";
  if (valor < 60) return "bg-amber-500/80";
  if (valor < 75) return "bg-yellow-400/80";
  return "bg-emerald-500/75";
}

export default function DiagnosticoDetalheClient({ id }: { id: string }) {
  const [data, setData] = useState<DiagnosticoDetalheApi | null>(null);
  const [error, setError] = useState<string | null>(null);
  const versaoOtimistaRef = useRef<number | null>(null);
  const lastSyncedM12Ref = useRef<string | null>(null);

  useEffect(() => {
    let cancel = false;
    (async () => {
      const token = getAccessToken();
      const base = getApiUrl().replace(/\/$/, "");
      try {
        const res = await fetch(`${base}/diagnosticos/${id}`, {
          headers: {
            Accept: "application/json",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
          cache: "no-store",
        });
        if (!res.ok) {
          if (!cancel) {
            setError(`API ${res.status}`);
            setData(mockDiagnostico(id));
          }
          return;
        }
        const json = (await res.json()) as DiagnosticoDetalheApi;
        if (!cancel) {
          if (json.versao_otimista != null) {
            versaoOtimistaRef.current = json.versao_otimista;
          }
          setData(json);
          setError(null);
        }
      } catch {
        if (!cancel) {
          setError("Falha de rede — exibindo dados de exemplo.");
          setData(mockDiagnostico(id));
        }
      }
    })();
    return () => {
      cancel = true;
    };
  }, [id]);

  const radarData = useMemo(() => {
    if (!data?.score?.score_por_dimensao) return null;
    return Object.entries(data.score.score_por_dimensao).map(([dim, s]) => ({
      dimensao: dim.replace(/_/g, " "),
      valor: s.valor,
    }));
  }, [data]);

  const rankingGaps = useMemo(() => {
    if (!data?.score?.score_por_dimensao) return [];
    return Object.entries(data.score.score_por_dimensao)
      .map(([dim, s]) => ({
        dimensao: dim.replace(/_/g, " "),
        valor: s.valor,
      }))
      .sort((a, b) => a.valor - b.valor);
  }, [data]);

  /** M12 — frente checklist ABNT 10 itens (mesmo texto retornado pela API). */
  const frenteAbnt10 = useMemo(() => {
    return (
      data?.checklist?.find((f) => f.nome.includes("17301") && f.nome.includes("10")) ?? null
    );
  }, [data?.checklist]);

  const [abntChecks, setAbntChecks] = useState<boolean[]>([]);

  useEffect(() => {
    if (!frenteAbnt10 || frenteAbnt10.acoes.length === 0) return;
    const n = frenteAbnt10.acoes.length;
    const fromApi = data?.checklist_m12_autoconf;
    if (fromApi && fromApi.length === n) {
      setAbntChecks(fromApi);
      lastSyncedM12Ref.current = JSON.stringify(fromApi);
      return;
    }
    const zeros = Array.from({ length: n }, () => false);
    setAbntChecks(zeros);
    lastSyncedM12Ref.current = JSON.stringify(zeros);
  }, [data?.checklist_m12_autoconf, frenteAbnt10]);

  useEffect(() => {
    if (data?.versao_otimista != null) {
      versaoOtimistaRef.current = data.versao_otimista;
    }
  }, [data?.versao_otimista]);

  const refetchDetalhe = useCallback(async () => {
    const token = getAccessToken();
    const base = getApiUrl().replace(/\/$/, "");
    const res = await fetch(`${base}/diagnosticos/${id}`, {
      headers: {
        Accept: "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      cache: "no-store",
    });
    if (!res.ok) return;
    const json = (await res.json()) as DiagnosticoDetalheApi;
    if (json.versao_otimista != null) {
      versaoOtimistaRef.current = json.versao_otimista;
    }
    setData(json);
  }, [id]);

  useEffect(() => {
    if (!data || data.status !== "finalizado") return;
    if (abntChecks.length !== 10) return;
    const serialized = JSON.stringify(abntChecks);
    if (serialized === lastSyncedM12Ref.current) return;

    const token = getAccessToken();
    if (!token) return;

    const handle = window.setTimeout(() => {
      void (async () => {
        const v = versaoOtimistaRef.current;
        if (v == null) return;
        const base = getApiUrl().replace(/\/$/, "");
        const res = await fetch(`${base}/diagnosticos/${id}/checklist-m12-autoconf`, {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
            Accept: "application/json",
            Authorization: `Bearer ${token}`,
            "If-Match": String(v),
          },
          body: JSON.stringify({ checklist_m12_autoconf: abntChecks }),
        });
        if (res.ok) {
          const json = (await res.json()) as DiagnosticoDetalheApi;
          if (json.versao_otimista != null) {
            versaoOtimistaRef.current = json.versao_otimista;
          }
          const m12 = json.checklist_m12_autoconf;
          lastSyncedM12Ref.current = JSON.stringify(
            m12 && m12.length === 10 ? m12 : abntChecks,
          );
          setData(json);
          return;
        }
        if (res.status === 412) {
          await refetchDetalhe();
        }
      })();
    }, 480);

    return () => window.clearTimeout(handle);
  }, [abntChecks, data, id, refetchDetalhe]);

  const barGapColors = ["#b91c1c", "#ea580c", "#ca8a04", "#65a30d", "#16a34a"];

  if (!data) {
    return (
      <div className="container py-10 text-muted-foreground">
        Carregando diagnóstico…
      </div>
    );
  }

  return (
    <div className="container py-10">
      <div className="mb-8">
        <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-sm mb-4">
          <Link href="/dashboard" className="text-primary hover:underline">
            ← Voltar para Dashboard
          </Link>
          <span className="text-muted-foreground">·</span>
          <Link href="/abnt-framework" className="text-primary hover:underline">
            Guia ABNT / PDCA (M11)
          </Link>
        </div>
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <h1 className="text-3xl font-bold">{data.empresa_razao_social}</h1>
            <p className="text-muted-foreground">ID do Diagnóstico: {data.id}</p>
            {error && (
              <p className="text-sm text-amber-600 mt-2">
                {error} — dados podem ser mock locais.
              </p>
            )}
          </div>
          <div className="flex flex-wrap gap-2 items-center">
            <Badge variant={data.plano === "gratuito" ? "secondary" : "default"} className="text-sm px-4 py-1">
              PLANO {data.plano.toUpperCase()}
            </Badge>
            {data.relatorio_pdf_url && (
              <Button variant="default" size="sm" asChild>
                <a href={data.relatorio_pdf_url} target="_blank" rel="noopener noreferrer">
                  Abrir relatório PDF
                </a>
              </Button>
            )}
          </div>
        </div>
      </div>

      {radarData && radarData.length > 0 && (
        <Card className="mb-10">
          <CardHeader>
            <CardTitle>Radar por dimensão</CardTitle>
          </CardHeader>
          <CardContent className="h-[340px]">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart data={radarData} cx="50%" cy="50%" outerRadius="80%">
                <PolarGrid />
                <PolarAngleAxis dataKey="dimensao" tick={{ fontSize: 11 }} />
                <Radar name="Score" dataKey="valor" stroke="#2563eb" fill="#3b82f6" fillOpacity={0.35} />
              </RadarChart>
            </ResponsiveContainer>
            {data.score?.score_geral && (
              <p className="text-center text-sm text-muted-foreground mt-2">
                Score geral: <strong>{data.score.score_geral.valor}</strong> / 100
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {rankingGaps.length > 0 && (
        <div className="grid md:grid-cols-2 gap-8 mb-10">
          <Card>
            <CardHeader>
              <CardTitle>Heatmap rápido por dimensão (M05)</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground mb-4">
                Intensidade da cor: menor score (vermelho) = maior gap relativo no diagnóstico.
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {rankingGaps.map((row) => (
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
            <CardHeader>
              <CardTitle>Ranking de gaps (menores scores)</CardTitle>
            </CardHeader>
            <CardContent className="h-[280px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={rankingGaps}
                  layout="vertical"
                  margin={{ left: 8, right: 16 }}
                >
                  <XAxis type="number" domain={[0, 100]} />
                  <YAxis type="category" dataKey="dimensao" width={120} tick={{ fontSize: 11 }} />
                  <Tooltip
                    formatter={(v) => [
                      `${typeof v === "number" ? v.toFixed(1) : String(v ?? "")} / 100`,
                      "Score",
                    ]}
                  />
                  <Bar dataKey="valor" radius={[0, 4, 4, 0]}>
                    {rankingGaps.map((_, i) => (
                      <Cell key={i} fill={barGapColors[Math.min(i, barGapColors.length - 1)]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>
      )}

      {data.cronograma && data.cronograma.length > 0 && (
        <Card className="mb-10">
          <CardHeader>
            <CardTitle>Cronograma em cinco horizontes (LC 214/2025)</CardTitle>
          </CardHeader>
          <CardContent className="overflow-x-auto">
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2 pr-4">Fase</th>
                  <th className="text-left py-2 pr-4">Foco</th>
                  <th className="text-left py-2">Referência normativa</th>
                </tr>
              </thead>
              <tbody>
                {data.cronograma.map((linha) => (
                  <tr key={linha.fase} className="border-b border-muted">
                    <td className="py-2 pr-4 font-medium align-top">{linha.fase}</td>
                    <td className="py-2 pr-4 align-top">{linha.foco}</td>
                    <td className="py-2 text-muted-foreground align-top italic">{linha.referencia_normativa}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="mt-8">
              <p className="text-sm font-semibold mb-4">Linha do tempo (M06 — visão rápida)</p>
              <ol className="relative border-l-2 border-primary/35 ml-3 space-y-8 pl-6">
                {(data.cronograma ?? []).map((linha) => (
                  <li key={linha.fase} className="relative">
                    <span className="absolute -left-[21px] top-1.5 flex h-3 w-3 rounded-full bg-primary ring-4 ring-background" />
                    <p className="font-medium text-sm">{linha.fase}</p>
                    <p className="text-sm text-muted-foreground mt-1">{linha.foco}</p>
                    <p className="text-xs text-muted-foreground italic mt-1">{linha.referencia_normativa}</p>
                  </li>
                ))}
              </ol>
            </div>
          </CardContent>
        </Card>
      )}

      {frenteAbnt10 && frenteAbnt10.acoes.length > 0 && (
        <Card className="mb-10">
          <CardHeader>
            <CardTitle>Autoconferência ABNT — 10 controles (M12)</CardTitle>
            <p className="text-sm font-normal text-muted-foreground">
              Réplica espelho do checklist do relatório PDF. Alterações são salvas no servidor com
              concorrência otimista (<code className="text-xs">If-Match</code> /{" "}
              <code className="text-xs">versao_otimista</code>), alinhado à ABNT NBR 17301:2026 e LC 214/2025.
            </p>
          </CardHeader>
          <CardContent className="space-y-3">
            {frenteAbnt10.acoes.map((a, i) => (
              <label
                key={a.descricao + String(i)}
                className="flex gap-3 items-start rounded-lg border bg-muted/10 p-3 cursor-pointer hover:border-primary/40"
              >
                <input
                  type="checkbox"
                  className="mt-1 h-4 w-4 rounded border-input"
                  checked={abntChecks[i] ?? false}
                  onChange={(e) => {
                    setAbntChecks((prev) => {
                      const next = [...prev];
                      next[i] = e.target.checked;
                      return next;
                    });
                  }}
                />
                <span className="text-sm leading-snug">{a.descricao}</span>
              </label>
            ))}
          </CardContent>
        </Card>
      )}

      {data.matriz_impacto && data.matriz_impacto.length > 0 && (
        <Card className="mb-10">
          <CardHeader>
            <CardTitle>Matriz de impacto por departamento</CardTitle>
          </CardHeader>
          <CardContent className="overflow-x-auto">
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2 pr-4">Departamento</th>
                  <th className="text-left py-2 pr-4">Impacto</th>
                  <th className="text-left py-2 pr-4">Criticidade</th>
                  <th className="text-left py-2">Base legal</th>
                </tr>
              </thead>
              <tbody>
                {data.matriz_impacto.map((m) => (
                  <tr key={m.departamento} className="border-b border-muted">
                    <td className="py-2 pr-4 font-medium">{m.departamento}</td>
                    <td className="py-2 pr-4">{m.impacto_resumo}</td>
                    <td className="py-2 pr-4">
                      <Badge variant={m.criticidade === "Crítica" ? "destructive" : "secondary"}>
                        {m.criticidade}
                      </Badge>
                    </td>
                    <td className="py-2 text-muted-foreground text-xs">{m.base_legal ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>
      )}

      <div className="space-y-8">
        <div className="flex justify-between items-center flex-wrap gap-4">
          <h2 className="text-2xl font-bold tracking-tight">Quadro de implantação</h2>
          <Button variant="outline" type="button" disabled>
            Exportar CSV (em breve)
          </Button>
        </div>

        <div className="flex gap-6 overflow-x-auto pb-4">
          <div className="flex-1 min-w-[320px] bg-slate-100 rounded-lg p-4">
            <h3 className="font-semibold text-slate-700 mb-4 flex items-center justify-between">
              Ações sugeridas
              <Badge variant="secondary">
                {data.checklist?.reduce((acc, f) => acc + f.acoes.length, 0) ?? 0}
              </Badge>
            </h3>
            <div className="space-y-3">
              {data.checklist?.map((frente, i) => (
                <div key={i}>
                  <div className="text-xs font-bold text-slate-500 uppercase mb-2 mt-4 first:mt-0">
                    {frente.nome}
                  </div>
                  {frente.acoes.map((acao, j) => (
                    <Card
                      key={j}
                      className="mb-2 hover:border-primary/50 transition-colors"
                    >
                      <CardHeader className="p-4 pb-2">
                        <div className="flex items-start justify-between gap-2">
                          <CardTitle className="text-sm font-medium leading-tight">
                            {acao.descricao}
                          </CardTitle>
                          {acao.prioridade != null && (
                            <Badge variant="outline" className="shrink-0 text-[10px]">
                              #{acao.prioridade}
                            </Badge>
                          )}
                        </div>
                        {acao.base_legal && (
                          <p className="text-xs text-muted-foreground mt-1">
                            Base legal: {acao.base_legal}
                          </p>
                        )}
                      </CardHeader>
                      <CardContent className="p-4 pt-0">
                        <div className="flex justify-between items-center mt-2">
                          <span className="text-xs text-muted-foreground">{acao.responsavel}</span>
                          <Badge
                            variant={acao.criticidade === "Crítica" ? "destructive" : "secondary"}
                            className="text-[10px]"
                          >
                            {acao.criticidade}
                          </Badge>
                        </div>
                        <p className="text-xs text-muted-foreground mt-1">Prazo: {acao.prazo}</p>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
