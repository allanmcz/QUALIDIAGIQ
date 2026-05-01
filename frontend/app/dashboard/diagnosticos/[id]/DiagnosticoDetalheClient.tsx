"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  PolarAngleAxis,
  PolarGrid,
  Radar,
  RadarChart,
  ResponsiveContainer,
} from "recharts";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getAccessToken, getApiUrl } from "@/lib/api/config";

type Acao = {
  descricao: string;
  responsavel: string;
  prazo: string;
  criticidade: string;
  base_legal?: string | null;
};
type Frente = { nome: string; acoes: Acao[] };

type DiagnosticoData = {
  id: string;
  empresa_razao_social: string;
  plano: string;
  status: string;
  checklist: Frente[] | null;
  score: {
    score_geral: { valor: number };
    score_por_dimensao: Record<string, { valor: number; peso_total_aplicado: number }>;
  } | null;
};

function mockDiagnostico(id: string): DiagnosticoData {
  const isAvancado = id.startsWith("7");
  return {
    id,
    empresa_razao_social: isAvancado ? "Acme Corp S/A" : "Tech Solutions Ltda",
    plano: isAvancado ? "avancado" : "gratuito",
    status: "finalizado",
    score: null,
    checklist: [
      {
        nome: "Governança e Comitê",
        acoes: [
          {
            descricao: "Constituir Comitê Tributário Reforma",
            responsavel: "Diretoria",
            prazo: "Out/2025",
            criticidade: "Crítica",
          },
        ],
      },
    ],
  };
}

export default function DiagnosticoDetalheClient({ id }: { id: string }) {
  const [data, setData] = useState<DiagnosticoData | null>(null);
  const [error, setError] = useState<string | null>(null);

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
        const json = (await res.json()) as DiagnosticoData;
        if (!cancel) {
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

  if (!data) {
    return (
      <div className="container py-10 text-muted-foreground">
        Carregando diagnóstico…
      </div>
    );
  }

  const radarData =
    data.score?.score_por_dimensao &&
    Object.entries(data.score.score_por_dimensao).map(([dim, s]) => ({
      dimensao: dim.replace(/_/g, " "),
      valor: s.valor,
    }));

  return (
    <div className="container py-10">
      <div className="mb-8">
        <Link href="/dashboard" className="text-sm text-primary hover:underline mb-4 inline-block">
          &larr; Voltar para Dashboard
        </Link>
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
          <Badge variant={data.plano === "gratuito" ? "secondary" : "default"} className="text-sm px-4 py-1">
            PLANO {data.plano.toUpperCase()}
          </Badge>
        </div>
      </div>

      {radarData && radarData.length > 0 && (
        <Card className="mb-10">
          <CardHeader>
            <CardTitle>Radar por dimensão (M05 — visão rápida)</CardTitle>
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
                        <CardTitle className="text-sm font-medium leading-tight">
                          {acao.descricao}
                        </CardTitle>
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
