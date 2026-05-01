"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import {
  fetchManifestoPesosPublic,
  fetchMetodologiaPublic,
  type ManifestoPesosPublic,
  type MetodologiaPublic,
} from "@/lib/api/metodologia_public";
import { getApiUrl } from "@/lib/api/config";

function TabelaPesosMacro({ titulo, pesos }: { titulo: string; pesos: Record<string, number> }) {
  const linhas = Object.entries(pesos).sort(([a], [b]) => a.localeCompare(b));
  return (
    <div className="space-y-2">
      <h3 className="text-lg font-semibold">{titulo}</h3>
      <div className="overflow-x-auto rounded-md border">
        <table className="w-full text-sm">
          <thead className="bg-muted/50">
            <tr>
              <th className="text-left p-3 font-medium">Dimensão</th>
              <th className="text-right p-3 font-medium">Peso macro</th>
            </tr>
          </thead>
          <tbody>
            {linhas.map(([dim, peso]) => (
              <tr key={dim} className="border-t">
                <td className="p-3 font-mono text-xs">{dim}</td>
                <td className="p-3 text-right tabular-nums">{peso}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default function MetodologiaPage() {
  const [meta, setMeta] = useState<MetodologiaPublic | null>(null);
  const [manifesto, setManifesto] = useState<ManifestoPesosPublic | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(true);

  useEffect(() => {
    let cancel = false;
    async function load() {
      setCarregando(true);
      setErro(null);
      try {
        const [m, man] = await Promise.all([fetchMetodologiaPublic(), fetchManifestoPesosPublic()]);
        if (!cancel) {
          setMeta(m);
          setManifesto(man);
        }
      } catch (e) {
        if (!cancel) {
          setErro(e instanceof Error ? e.message : "Falha ao carregar dados da API.");
          setMeta(null);
          setManifesto(null);
        }
      } finally {
        if (!cancel) setCarregando(false);
      }
    }
    load();
    return () => {
      cancel = true;
    };
  }, []);

  const baseApi = getApiUrl().replace(/\/$/, "");

  return (
    <div className="container max-w-5xl py-10 space-y-10">
      <div>
        <Link href="/wizard" className="text-sm text-primary hover:underline">
          ← Wizard de diagnóstico
        </Link>
      </div>

      <header className="space-y-2">
        <p className="text-xs uppercase tracking-wide text-muted-foreground font-semibold">
          Transparência metodológica (M03)
        </p>
        <h1 className="text-3xl font-bold tracking-tight">Metodologia e manifesto de pesos</h1>
        <p className="text-muted-foreground leading-relaxed max-w-3xl">
          Conteúdo obtido em tempo real dos endpoints públicos da API QualiDiagIQ — mesmo motor usado no
          cálculo do score (sem JWT). Fontes normativas de referência: EC 132/2023, LC 214/2025, ABNT NBR
          17301:2026.
        </p>
        <p className="text-sm text-muted-foreground">
          JSON bruto:{" "}
          <a
            href={`${baseApi}/diagnosticos/metodologia`}
            className="text-primary underline font-medium"
            target="_blank"
            rel="noopener noreferrer"
          >
            /diagnosticos/metodologia
          </a>
          {" · "}
          <a
            href={`${baseApi}/diagnosticos/manifesto-pesos`}
            className="text-primary underline font-medium"
            target="_blank"
            rel="noopener noreferrer"
          >
            /diagnosticos/manifesto-pesos
          </a>
        </p>
      </header>

      {carregando && (
        <p className="text-sm text-muted-foreground" aria-live="polite">
          Carregando metodologia e manifesto…
        </p>
      )}

      {erro && (
        <div className="rounded-lg border border-destructive/40 bg-destructive/10 p-4 text-sm text-destructive">
          <p className="font-medium">Não foi possível contactar a API.</p>
          <p className="mt-1">{erro}</p>
          <p className="mt-2 text-xs opacity-90">
            Confira se o backend está no ar e se <code className="bg-background/50 px-1 rounded">NEXT_PUBLIC_API_URL</code>{" "}
            aponta para a base correta (padrão compose: <code className="bg-background/50 px-1 rounded">http://localhost:60000</code>
            ).
          </p>
        </div>
      )}

      {!carregando && meta && (
        <section className="space-y-6 rounded-xl border bg-card p-6">
          <div>
            <h2 className="text-xl font-semibold">Referência normativa declarada</h2>
            <p className="mt-1 text-sm text-muted-foreground">{meta.versao_normativa}</p>
          </div>
          <TabelaPesosMacro titulo="Pesos macro — agregação do score geral (0–100)" pesos={meta.pesos_macro_dimensao_score_geral} />
          <div className="space-y-2">
            <h3 className="text-lg font-semibold">Nota metodológica</h3>
            <p className="text-sm leading-relaxed text-muted-foreground whitespace-pre-wrap">{meta.nota_metodologica}</p>
          </div>
          {meta.recomendacoes_gaps_criticos.length > 0 && (
            <div className="space-y-2">
              <h3 className="text-lg font-semibold">Alertas heurísticos (leitura executiva)</h3>
              <ul className="list-disc list-inside text-sm text-muted-foreground space-y-1">
                {meta.recomendacoes_gaps_criticos.map((r, i) => (
                  <li key={`${i}-${r.slice(0, 24)}`}>{r}</li>
                ))}
              </ul>
            </div>
          )}
        </section>
      )}

      {!carregando && manifesto && (
        <section className="space-y-6 rounded-xl border bg-card p-6">
          <div className="flex flex-wrap gap-4 justify-between items-baseline">
            <h2 className="text-xl font-semibold">Manifesto por pergunta</h2>
            <p className="text-xs text-muted-foreground font-mono">
              catálogo {manifesto.versao_catalogo} · manifesto {manifesto.versao_manifesto}
            </p>
          </div>
          <div className="space-y-2">
            <h3 className="text-lg font-semibold">Fórmula do score geral</h3>
            <p className="text-sm leading-relaxed text-muted-foreground whitespace-pre-wrap">{manifesto.formula_score_geral}</p>
          </div>
          <div className="space-y-2">
            <h3 className="text-lg font-semibold">Calibração (M02)</h3>
            <p className="text-sm leading-relaxed text-muted-foreground whitespace-pre-wrap">{manifesto.nota_calibracao_m02}</p>
          </div>
          <TabelaPesosMacro titulo="Pesos macro (manifesto — espelho do domínio)" pesos={manifesto.pesos_macro_dimensao} />
          <div className="space-y-2">
            <h3 className="text-lg font-semibold">Catálogo ({manifesto.perguntas.length} itens)</h3>
            <div className="overflow-x-auto rounded-md border max-h-[min(480px,60vh)] overflow-y-auto">
              <table className="w-full text-sm">
                <thead className="bg-muted/50 sticky top-0">
                  <tr>
                    <th className="text-left p-2 font-medium">Código</th>
                    <th className="text-left p-2 font-medium">Dimensão</th>
                    <th className="text-left p-2 font-medium">Tipo</th>
                    <th className="text-right p-2 font-medium">Peso</th>
                    <th className="text-left p-2 font-medium">Base legal</th>
                  </tr>
                </thead>
                <tbody>
                  {[...manifesto.perguntas]
                    .sort((a, b) => a.codigo.localeCompare(b.codigo))
                    .map((p) => (
                      <tr key={p.codigo} className="border-t">
                        <td className="p-2 font-mono text-xs whitespace-nowrap">{p.codigo}</td>
                        <td className="p-2 font-mono text-xs">{p.dimensao}</td>
                        <td className="p-2 font-mono text-xs">{p.tipo}</td>
                        <td className="p-2 text-right tabular-nums">{p.peso}</td>
                        <td className="p-2 text-xs text-muted-foreground max-w-xs">{p.base_legal ?? "—"}</td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>
      )}

      <p className="text-xs text-muted-foreground">
        <Link href="/abnt-framework" className="text-primary underline">
          M11 — framework ABNT no produto
        </Link>
      </p>
    </div>
  );
}
