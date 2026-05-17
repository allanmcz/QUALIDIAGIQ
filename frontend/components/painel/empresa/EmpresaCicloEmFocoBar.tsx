"use client";

import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { normalizarHrefRelatorioPdf } from "@/lib/api/config";
import { hrefPrivacidadePainel } from "@/lib/painel/privacidade_diagnostico_query";
import type { DiagnosticoResumoApi } from "@/lib/api/lista_diagnosticos";
import type { DiagnosticoDetalheApi } from "@/types/diagnostico_detalhe";

type Props = {
  detalhe: DiagnosticoDetalheApi;
  resumo?: DiagnosticoResumoApi | null;
};

/**
 * Barra contextual do ciclo expandido — plano, PDF e atalhos por diagnóstico (ex-ficha `/diagnosticos/[id]`).
 */
export function EmpresaCicloEmFocoBar({ detalhe, resumo }: Props) {
  const score = detalhe.score?.score_geral?.valor ?? resumo?.score_geral ?? null;
  const quando = new Date(detalhe.finalizado_em ?? detalhe.criado_em ?? resumo?.finalizado_em ?? resumo?.criado_em ?? Date.now()).toLocaleDateString(
    "pt-BR",
    { day: "2-digit", month: "2-digit", year: "numeric" },
  );

  return (
    <section
      id="empresa-ciclo-em-foco"
      className="rounded-lg border border-border/80 bg-muted/20 px-4 py-4 space-y-3 scroll-mt-20"
      aria-label="Ciclo em foco no painel"
    >
      <p className="text-sm text-muted-foreground">
        Ciclo em foco
        {score != null ? (
          <>
            {" "}
            · Score <span className="font-medium text-foreground tabular-nums">{score.toFixed(1)}</span>
          </>
        ) : null}
        {" "}
        · <span className="tabular-nums">{quando}</span>
      </p>
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant={detalhe.plano === "gratuito" ? "secondary" : "default"} className="text-xs px-3 py-0.5">
          PLANO {detalhe.plano.toUpperCase()}
        </Badge>
        {detalhe.relatorio_pdf_url ? (
          <Button variant="default" size="sm" className="shrink-0" asChild>
            <a
              href={normalizarHrefRelatorioPdf(detalhe.relatorio_pdf_url) ?? detalhe.relatorio_pdf_url}
              target="_blank"
              rel="noopener noreferrer"
            >
              Abrir relatório PDF
            </a>
          </Button>
        ) : null}
      </div>
      <nav
        className="flex flex-wrap items-center gap-2 text-sm"
        aria-label="Atalhos do ciclo em foco"
      >
        <Button variant="outline" size="sm" className="shrink-0" asChild>
          <Link href={hrefPrivacidadePainel({ diagnosticoId: detalhe.id, secao: "lgpd" })}>
            Privacidade LGPD
          </Link>
        </Button>
        <Button variant="outline" size="sm" className="shrink-0" asChild>
          <Link href={hrefPrivacidadePainel({ diagnosticoId: detalhe.id, secao: "retificacoes" })}>
            Retificações
          </Link>
        </Button>
        <Button variant="outline" size="sm" className="shrink-0" asChild>
          <Link href={`#diag-explicacao-score-llm`}>Explicação IA</Link>
        </Button>
        <span className="text-muted-foreground hidden sm:inline" aria-hidden>
          ·
        </span>
        <Link href="/abnt-framework" className="text-primary hover:underline shrink-0">
          Guia ABNT / PDCA (M11)
        </Link>
      </nav>
    </section>
  );
}
