"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import { RefreshCw } from "lucide-react";

import { EmpresaDiagnosticosListaPainel } from "@/components/painel/empresa/EmpresaDiagnosticosListaPainel";
import { EmpresaQuadroImplantacaoTopo } from "@/components/painel/empresa/EmpresaQuadroImplantacaoTopo";
import { fetchDiagnosticoDetalhe } from "@/lib/api/fetch_diagnostico_detalhe";
import {
  fetchDiagnosticosResumoTodasPaginasPorEmpresa,
  type DiagnosticoResumoApi,
} from "@/lib/api/lista_diagnosticos";
import { temSessaoPainelParaApiCliente } from "@/lib/api/config";
import { idDiagnosticoBaselineQuadroEmpresa } from "@/lib/painel/diagnostico_empresa_ordem";
import { hrefPrivacidadePainel } from "@/lib/painel/privacidade_diagnostico_query";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  cabecalhosAuthPainelOpcional,
  getApiUrlForFetch,
  normalizarHrefRelatorioPdf,
} from "@/lib/api/config";
import { encerrarSessaoPainelSe401 } from "@/lib/auth/painel_session";
import {
  buildEmpresaDiagnosticosHref,
  buildWizardUrlNovaDiagnosticoEmpresa,
} from "@/lib/dashboard/empresa_diagnostico_urls";
import { navegarRefazerDiagnosticoPainel } from "@/lib/dashboard/refazer_diagnostico_painel";
import { clearPendingDiagnosticoFromStorage } from "@/lib/wizard/pending_diagnostico";
import { clearWizardDraft } from "@/lib/wizard/wizard_draft";
import type { DiagnosticoDetalheApi } from "@/types/diagnostico_detalhe";

export type { DiagnosticoDetalheApi, QuadroItemPersistidoApi } from "@/types/diagnostico_detalhe";

function mockDiagnostico(id: string): DiagnosticoDetalheApi {
  const isAvancado = id.startsWith("7");
  return {
    id,
    empresa_razao_social: isAvancado ? "Acme Corp S/A" : "Tech Solutions Ltda",
    empresa_cnpj: "12345678000195",
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
    quadro_implantacao_anotacoes: null,
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

export default function DiagnosticoDetalheClient({ id }: { id: string }) {
  const router = useRouter();
  const [data, setData] = useState<DiagnosticoDetalheApi | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [listaEmpresa, setListaEmpresa] = useState<DiagnosticoResumoApi[] | null>(null);
  const [detalhesEmpresa, setDetalhesEmpresa] = useState<Record<string, DiagnosticoDetalheApi>>({});
  useEffect(() => {
    let cancel = false;
    (async () => {
      const base = getApiUrlForFetch().replace(/\/$/, "");
      try {
        const res = await fetch(`${base}/diagnosticos/${id}`, {
          headers: {
            Accept: "application/json",
            ...cabecalhosAuthPainelOpcional(),
          },
          cache: "no-store",
          credentials: "include",
        });
        if (!res.ok) {
          if (encerrarSessaoPainelSe401(res.status)) return;
          if (!cancel) {
            setError("Não foi possível atualizar os dados deste diagnóstico agora.");
            setData(mockDiagnostico(id));
          }
          return;
        }
        const json = (await res.json()) as DiagnosticoDetalheApi;
        if (!cancel) {
          setData(json);
          setError(null);
        }
      } catch {
        if (!cancel) {
          setError("Conexão temporariamente indisponível. Exibindo uma prévia local para consulta.");
          setData(mockDiagnostico(id));
        }
      }
    })();
    return () => {
      cancel = true;
    };
  }, [id]);

  const aoDetalheEmpresaAtualizado = useCallback((d: DiagnosticoDetalheApi) => {
    setDetalhesEmpresa((prev) => ({ ...prev, [d.id]: d }));
  }, []);

  const listaParaQuadro = useMemo((): DiagnosticoResumoApi[] | null => {
    if (listaEmpresa?.length) return listaEmpresa;
    if (!data) return null;
    const cnpj = (data.empresa_cnpj ?? "").replace(/\D/g, "").trim();
    const criado = (data.criado_em && String(data.criado_em).trim()) || "1970-01-01T00:00:00.000Z";
    return [
      {
        id: data.id,
        empresa_razao_social: data.empresa_razao_social,
        ...(cnpj.length === 14 ? { empresa_cnpj: cnpj } : {}),
        status: data.status,
        plano: data.plano,
        score_geral: data.score?.score_geral?.valor ?? null,
        criado_em: criado,
        finalizado_em: data.finalizado_em ?? null,
        relatorio_pdf_url: data.relatorio_pdf_url,
        versao_otimista: data.versao_otimista ?? null,
        painel_estado_ciclo: data.painel_estado_ciclo ?? null,
      },
    ];
  }, [listaEmpresa, data]);

  const cnpjParaLista = (data?.empresa_cnpj ?? "").replace(/\D/g, "");

  /** Lista e detalhe do quadro no pai — evita setState no pai durante render do filho. */
  useEffect(() => {
    if (cnpjParaLista.length !== 14 || !temSessaoPainelParaApiCliente()) return;
    let cancel = false;
    void fetchDiagnosticosResumoTodasPaginasPorEmpresa(cnpjParaLista).then((rows) => {
      if (!cancel) setListaEmpresa(rows);
    });
    return () => {
      cancel = true;
    };
  }, [cnpjParaLista, data?.id]);

  useEffect(() => {
    if (!listaEmpresa?.length) return;
    const baselineId = idDiagnosticoBaselineQuadroEmpresa(listaEmpresa);
    if (!baselineId) return;
    let cancel = false;
    void fetchDiagnosticoDetalhe(baselineId).then((d) => {
      if (!cancel) {
        setDetalhesEmpresa((prev) => (prev[baselineId] ? prev : { ...prev, [d.id]: d }));
      }
    });
    return () => {
      cancel = true;
    };
  }, [listaEmpresa]);

  if (!data) {
    return (
      <div className="container py-10 text-muted-foreground">
        Carregando diagnóstico…
      </div>
    );
  }

  const cnpjDigits = (data.empresa_cnpj ?? "").replace(/\D/g, "");
  const temCnpj14 = cnpjDigits.length === 14;

  const detalhesEmpresaComAtual = { ...detalhesEmpresa, [data.id]: data };

  return (
    <div className="container py-10">
      <div className="mb-8">
        <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-sm mb-4">
          <Link href="/dashboard/diagnosticos" className="text-primary hover:underline">
            ← Voltar para Dashboard
          </Link>
          <span className="text-muted-foreground">·</span>
          <Link href="/abnt-framework" className="text-primary hover:underline">
            Guia ABNT / PDCA (M11)
          </Link>
        </div>
        <nav
          className="flex flex-wrap gap-2 mb-4"
          aria-label="Atalhos para seções desta ficha"
        >
          <Button variant="outline" size="sm" asChild>
            <Link href={hrefPrivacidadePainel({ diagnosticoId: data.id, secao: "lgpd" })}>
              Privacidade LGPD
            </Link>
          </Button>
          <Button variant="outline" size="sm" asChild>
            <Link href={hrefPrivacidadePainel({ diagnosticoId: data.id, secao: "retificacoes" })}>
              Retificações
            </Link>
          </Button>
          <Button variant="outline" size="sm" asChild>
            <Link href="#diag-explicacao-score-llm">Explicação IA</Link>
          </Button>
        </nav>
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <h1 className="text-3xl font-bold">{data.empresa_razao_social}</h1>
            {error && (
              <p className="text-sm text-amber-600 mt-2">
                {error}
              </p>
            )}
          </div>
          <div className="flex flex-wrap gap-2 items-center">
            <Badge variant={data.plano === "gratuito" ? "secondary" : "default"} className="text-sm px-4 py-1">
              PLANO {data.plano.toUpperCase()}
            </Badge>
            {data.plano === "avancado" && !temCnpj14 ? (
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => {
                  clearWizardDraft();
                  clearPendingDiagnosticoFromStorage();
                  router.push("/wizard");
                }}
                className="gap-2"
              >
                <RefreshCw className="h-4 w-4 shrink-0" aria-hidden />
                Refazer diagnóstico
              </Button>
            ) : null}
            {data.relatorio_pdf_url && (
              <Button variant="default" size="sm" asChild>
                <a
                  href={normalizarHrefRelatorioPdf(data.relatorio_pdf_url) ?? data.relatorio_pdf_url}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Abrir relatório PDF
                </a>
              </Button>
            )}
          </div>
        </div>
      </div>

      {temCnpj14 ? (
        <Card className="mb-10 overflow-visible" id="painel-diagnosticos-mesma-empresa">
          <CardHeader className="pb-2">
            <CardTitle className="text-lg">Diagnósticos desta empresa no painel</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="mb-4">
              <Button
                type="button"
                variant="default"
                size="sm"
                onClick={() =>
                  navegarRefazerDiagnosticoPainel(
                    router,
                    buildWizardUrlNovaDiagnosticoEmpresa(cnpjDigits, data.empresa_razao_social),
                  )
                }
              >
                Novo ciclo de diagnóstico
              </Button>
            </div>
            <p className="text-sm text-muted-foreground mb-6 leading-relaxed">
              Ranking (M05), matriz de impacto e autoconferência ABNT (M12) são por diagnóstico — use{" "}
              <strong className="font-medium text-foreground">Expandir</strong> na linha. Gaps consolidados e
              plano de implantação ficam{" "}
              <strong className="font-medium text-foreground">no bloco abaixo</strong>
              {temCnpj14 ? (
                <>
                  {" "}
                  (ou na{" "}
                  <Link
                    href={buildEmpresaDiagnosticosHref(cnpjDigits, data.empresa_razao_social, {
                      hash: "empresa-implantacao-bloco",
                    })}
                    className="text-primary font-medium underline"
                  >
                    vista por CNPJ
                  </Link>
                  ).
                </>
              ) : null}
            </p>
            <EmpresaDiagnosticosListaPainel
              cnpjNormalizado={cnpjDigits}
              expandirDiagnosticoId={data.id}
              diagnosticoSemeado={data}
              usarExpandNaQuery={false}
              onListaDetalheAtualizado={aoDetalheEmpresaAtualizado}
            />
          </CardContent>
        </Card>
      ) : null}

      {temCnpj14 && listaParaQuadro?.length ? (
        <EmpresaQuadroImplantacaoTopo
          listaPainel={listaParaQuadro}
          detalhesPorId={detalhesEmpresaComAtual}
          onDataAtualizado={aoDetalheEmpresaAtualizado}
        />
      ) : null}

      {data.cronograma && data.cronograma.length > 0 && (
        <Card className="mb-10">
          <CardHeader>
            <CardTitle id="m06-cronograma-tabela-heading">
              Cronograma em cinco horizontes (LC 214/2025)
            </CardTitle>
          </CardHeader>
          <CardContent className="overflow-x-auto">
            <table
              className="w-full text-sm border-collapse"
              aria-labelledby="m06-cronograma-tabela-heading"
            >
              <thead>
                <tr className="border-b">
                  <th scope="col" className="text-left py-2 pr-4">
                    Fase
                  </th>
                  <th scope="col" className="text-left py-2 pr-4">
                    Foco
                  </th>
                  <th scope="col" className="text-left py-2">
                    Referência normativa
                  </th>
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
            <div
              className="mt-8 rounded-xl border border-border/80 bg-muted/25 p-5 sm:p-7 motion-reduce:transition-none"
              role="region"
              aria-label="Linha do tempo do cronograma em cinco fases (M06)"
            >
              <p
                id="m06-timeline-heading"
                className="text-sm font-semibold mb-6 tracking-tight text-foreground"
              >
                Linha do tempo (M06 — visão rápida)
              </p>
              <ol
                className="relative ml-2 border-l-[3px] border-primary/70 space-y-12 pl-8 sm:pl-11 motion-reduce:space-y-8"
                aria-labelledby="m06-timeline-heading"
              >
                {(data.cronograma ?? []).map((linha, idx) => (
                  <li
                    key={linha.fase}
                    className="relative scroll-mt-4 rounded-md outline-none focus-within:ring-2 focus-within:ring-primary/50 focus-within:ring-offset-2 focus-within:ring-offset-background"
                  >
                    <span
                      className="absolute -left-[26px] sm:-left-[30px] top-1 flex h-4 w-4 rounded-full bg-primary shadow-md ring-[3px] ring-background motion-reduce:shadow-none"
                      aria-hidden
                    />
                    <span className="sr-only">
                      Fase {idx + 1} de {(data.cronograma ?? []).length}
                    </span>
                    <p className="font-semibold text-sm leading-snug text-foreground">{linha.fase}</p>
                    <p className="text-sm text-muted-foreground mt-1.5 leading-relaxed">{linha.foco}</p>
                    <p className="text-xs text-muted-foreground mt-2 italic border-l-2 border-muted pl-3">
                      {linha.referencia_normativa}
                    </p>
                  </li>
                ))}
              </ol>
            </div>
          </CardContent>
        </Card>
      )}



    </div>
  );
}
