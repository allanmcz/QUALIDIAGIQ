"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  fetchManifestoPesosPublic,
  fetchMetodologiaPublic,
  type ManifestoPesosPublic,
  type MetodologiaPublic,
  type PesoMacroNormativaItemPublic,
} from "@/lib/api/metodologia_public";

/** Itens por página na tabela do catálogo (evita ~30 linhas de uma vez só). */
const CATALOGO_PAGE_SIZE = 10;

/** Rótulos comerciais PT-BR (slug da API → texto para diretoria/contabilidade). */
const ROTULO_DIMENSAO: Record<string, string> = {
  fiscal: "Fiscal",
  estrategica: "Estratégica",
  contabil: "Contábil",
  financeira: "Financeira",
  operacional: "Operacional",
  tecnologica: "Tecnológica",
  compliance_abnt_17301: "Compliance ABNT NBR 17301",
};

function rotuloDimensao(slug: string): string {
  return ROTULO_DIMENSAO[slug] ?? slug.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

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
              <th className="text-right p-3 font-medium">Peso no resultado final</th>
            </tr>
          </thead>
          <tbody>
            {linhas.map(([dim, peso]) => (
              <tr key={dim} className="border-t">
                <td className="p-3 text-sm">{rotuloDimensao(dim)}</td>
                <td className="p-3 text-right tabular-nums">{peso}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function TabelaPesosMacroVigencia({
  titulo,
  normativa,
}: {
  titulo: string;
  normativa: Record<string, PesoMacroNormativaItemPublic>;
}) {
  const linhas = Object.entries(normativa).sort(([a], [b]) => a.localeCompare(b));
  return (
    <div className="space-y-2">
      <h3 className="text-lg font-semibold">{titulo}</h3>
      <p className="text-xs text-muted-foreground">
        LC 214/2025 (previsibilidade) — linha normativa efetiva na data do pedido à API (UTC).
      </p>
      <div className="overflow-x-auto rounded-md border">
        <table className="w-full text-sm">
          <thead className="bg-muted/50">
            <tr>
              <th className="text-left p-3 font-medium">Dimensão</th>
              <th className="text-right p-3 font-medium">Peso</th>
              <th className="text-left p-3 font-medium">Início vigência</th>
              <th className="text-left p-3 font-medium">Fim vigência</th>
              <th className="text-left p-3 font-medium">Rótulo versão</th>
            </tr>
          </thead>
          <tbody>
            {linhas.map(([dim, row]) => (
              <tr key={dim} className="border-t">
                <td className="p-3 text-sm">{rotuloDimensao(dim)}</td>
                <td className="p-3 text-right tabular-nums">{row.peso}</td>
                <td className="p-3 text-xs tabular-nums whitespace-nowrap">{row.vigencia_inicio}</td>
                <td className="p-3 text-xs tabular-nums whitespace-nowrap">{row.vigencia_fim ?? "—"}</td>
                <td className="p-3 text-xs text-muted-foreground">{row.rotulo_versao ?? "—"}</td>
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
  const [paginaCatalogo, setPaginaCatalogo] = useState(0);

  const perguntasOrdenadas = useMemo(() => {
    if (!manifesto?.perguntas?.length) return [];
    return [...manifesto.perguntas].sort((a, b) => a.codigo.localeCompare(b.codigo));
  }, [manifesto]);

  const totalPaginasCatalogo = Math.max(1, Math.ceil(perguntasOrdenadas.length / CATALOGO_PAGE_SIZE));
  const paginaCatalogoVisivel = Math.min(
    Math.max(0, paginaCatalogo),
    Math.max(0, totalPaginasCatalogo - 1),
  );
  const inicioCatalogo = paginaCatalogoVisivel * CATALOGO_PAGE_SIZE;
  const perguntasPagina = perguntasOrdenadas.slice(inicioCatalogo, inicioCatalogo + CATALOGO_PAGE_SIZE);

  useEffect(() => {
    setPaginaCatalogo(0);
  }, [manifesto?.versao_manifesto, manifesto?.versao_catalogo, manifesto?.perguntas?.length]);

  useEffect(() => {
    setPaginaCatalogo((p) => Math.min(Math.max(0, p), Math.max(0, totalPaginasCatalogo - 1)));
  }, [totalPaginasCatalogo]);

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
          setErro(e instanceof Error ? e.message : "Verifique sua conexão e tente novamente.");
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

  return (
    <div className="container max-w-5xl py-10 space-y-10">
      <div>
        <Link href="/wizard" className="text-sm text-primary hover:underline font-medium">
          ← Iniciar diagnóstico
        </Link>
      </div>

      <header className="space-y-4">
        <p className="text-xs uppercase tracking-wide text-accent font-semibold">
          Metodologia auditável · QualiDiagIQ
        </p>
        <h1 className="text-3xl font-bold tracking-tight md:text-4xl">
          Como calculamos a sua maturidade tributária
        </h1>
        <p className="text-lg font-medium text-foreground max-w-3xl">
          Critérios públicos, pesos explícitos e base legal por pergunta — o mesmo motor que gera o seu
          relatório executivo.
        </p>
        <p className="text-muted-foreground leading-relaxed max-w-3xl text-base">
          Aqui você vê <strong className="text-foreground font-medium">o que avaliamos</strong>,{" "}
          <strong className="text-foreground font-medium">com que importância relativa</strong> e{" "}
          <strong className="text-foreground font-medium">em qual fundamento normativo</strong>, alinhados à{" "}
          <strong className="text-foreground font-medium">Reforma do Consumo</strong> (EC 132/2023, LC
          214/2025) e ao referencial <strong className="text-foreground font-medium">ABNT NBR 17301:2026</strong>
          — diferencial para governança, auditoria interna e decisões de investimento em adequação (CBS/IBS,
          processos e tecnologia).
        </p>
        <p className="text-sm text-muted-foreground max-w-3xl">
          Os valores são carregados da versão ativa do produto e coincidem com o assistente de diagnóstico no
          momento em que você conclui o questionário.
        </p>
      </header>

      {carregando && (
        <p className="text-sm text-muted-foreground" aria-live="polite">
          Preparando o conteúdo para você…
        </p>
      )}

      {erro && (
        <div className="rounded-lg border border-destructive/40 bg-destructive/10 p-4 text-sm text-destructive">
          <p className="font-medium text-foreground">Conteúdo temporariamente indisponível</p>
          <p className="mt-1">
            Não foi possível carregar os dados agora. Atualize a página ou tente de novo em alguns instantes.
          </p>
          <p className="mt-2 text-xs text-muted-foreground">{erro}</p>
        </div>
      )}

      {!carregando && meta && (
        <section className="space-y-6 rounded-xl border bg-card p-6 shadow-sm">
          <div>
            <h2 className="text-xl font-semibold text-foreground">Referência normativa e critério de score</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              Âncora de compliance: <span className="font-medium text-foreground">{meta.versao_normativa}</span>
            </p>
          </div>
          <TabelaPesosMacro
            titulo="Importância relativa de cada dimensão no índice final (0 a 100)"
            pesos={meta.pesos_macro_dimensao_score_geral}
          />
          <TabelaPesosMacroVigencia
            titulo="Vigência da normativa macro (rasto auditável)"
            normativa={meta.pesos_macro_dimensao_normativa}
          />
          <div className="space-y-2">
            <h3 className="text-lg font-semibold">Leitura executiva do modelo</h3>
            <p className="text-sm leading-relaxed text-muted-foreground whitespace-pre-wrap">{meta.nota_metodologica}</p>
          </div>
          {meta.recomendacoes_gaps_criticos.length > 0 && (
            <div className="space-y-2">
              <h3 className="text-lg font-semibold">Sinais para priorizar próximos passos</h3>
              <p className="text-xs text-muted-foreground">
                Orientações ilustrativas geradas pelo produto — não substituem assessoria jurídica ou contábil.
              </p>
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
        <section className="space-y-6 rounded-xl border bg-card p-6 shadow-sm">
          <div className="flex flex-wrap gap-4 justify-between items-baseline">
            <h2 className="text-xl font-semibold text-foreground">Manifesto de perguntas e transparência fiscal</h2>
            <p className="text-xs text-muted-foreground">
              Versão do questionário:{" "}
              <span className="font-medium text-foreground">{manifesto.versao_catalogo}</span>
              {" · "}
              Versão dos pesos aplicados:{" "}
              <span className="font-medium text-foreground">{manifesto.versao_manifesto}</span>
            </p>
          </div>
          <div className="space-y-2">
            <h3 className="text-lg font-semibold">Da resposta ao índice final</h3>
            <p className="text-sm leading-relaxed text-muted-foreground whitespace-pre-wrap">{manifesto.formula_score_geral}</p>
          </div>
          <div className="space-y-2">
            <h3 className="text-lg font-semibold">Previsibilidade e evolução do critério</h3>
            <p className="text-sm leading-relaxed text-muted-foreground whitespace-pre-wrap">{manifesto.nota_calibracao_m02}</p>
          </div>
          <TabelaPesosMacro titulo="Pesos por dimensão (detalhamento)" pesos={manifesto.pesos_macro_dimensao} />
          <TabelaPesosMacroVigencia
            titulo="Vigência aplicada aos pesos macro (mesmo critério da API)"
            normativa={manifesto.pesos_macro_dimensao_normativa}
          />
          <div className="space-y-3">
            <h3 className="text-lg font-semibold">
              Catálogo completo ({manifesto.perguntas.length}{" "}
              {manifesto.perguntas.length === 1 ? "pergunta" : "perguntas"})
            </h3>
            <p className="text-xs text-muted-foreground">
              Lista para consulta ({CATALOGO_PAGE_SIZE} por página). No diagnóstico, só entram as perguntas
              compatíveis com o perfil da sua empresa — porte, regime, setor e UF.
            </p>
            <div className="overflow-x-auto rounded-md border max-h-[min(520px,70vh)] overflow-y-auto">
              <table className="w-full text-sm">
                <thead className="bg-muted/50 sticky top-0">
                  <tr>
                    <th className="text-left p-2 font-medium">Ref.</th>
                    <th className="text-left p-2 font-medium">Dimensão</th>
                    <th className="text-left p-2 font-medium">Formato</th>
                    <th className="text-right p-2 font-medium">Peso</th>
                    <th className="text-left p-2 font-medium">Base legal</th>
                  </tr>
                </thead>
                <tbody>
                  {perguntasPagina.map((p) => (
                    <tr key={p.codigo} className="border-t">
                      <td className="p-2 text-xs whitespace-nowrap font-medium">{p.codigo}</td>
                      <td className="p-2 text-xs">{rotuloDimensao(p.dimensao)}</td>
                      <td className="p-2 text-xs capitalize">{p.tipo.replace(/_/g, " ")}</td>
                      <td className="p-2 text-right tabular-nums">{p.peso}</td>
                      <td className="p-2 text-xs text-muted-foreground max-w-xs">{p.base_legal ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {perguntasOrdenadas.length > CATALOGO_PAGE_SIZE && (
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <p className="text-sm text-muted-foreground tabular-nums" aria-live="polite">
                  Mostrando {inicioCatalogo + 1}–{Math.min(inicioCatalogo + perguntasPagina.length, perguntasOrdenadas.length)}{" "}
                  de {perguntasOrdenadas.length} · Página {paginaCatalogoVisivel + 1} de {totalPaginasCatalogo}
                </p>
                <div className="flex gap-2 shrink-0">
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    disabled={paginaCatalogoVisivel <= 0}
                    onClick={() =>
                      setPaginaCatalogo((p) => {
                        const cur = Math.min(Math.max(0, p), Math.max(0, totalPaginasCatalogo - 1));
                        return Math.max(0, cur - 1);
                      })
                    }
                  >
                    Anterior
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    disabled={paginaCatalogoVisivel >= totalPaginasCatalogo - 1}
                    onClick={() =>
                      setPaginaCatalogo((p) => {
                        const cur = Math.min(Math.max(0, p), Math.max(0, totalPaginasCatalogo - 1));
                        return Math.min(Math.max(0, totalPaginasCatalogo - 1), cur + 1);
                      })
                    }
                  >
                    Seguinte
                  </Button>
                </div>
              </div>
            )}
          </div>
        </section>
      )}

      <p className="text-sm text-muted-foreground">
        <Link href="/abnt-framework" className="text-primary underline font-medium">
          Saiba como o QualiDiagIQ alinha o produto à ABNT NBR 17301
        </Link>
      </p>
    </div>
  );
}
