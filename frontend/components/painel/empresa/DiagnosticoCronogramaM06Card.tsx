"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { DiagnosticoDetalheApi } from "@/types/diagnostico_detalhe";

type Props = {
  cronograma: NonNullable<DiagnosticoDetalheApi["cronograma"]>;
};

/**
 * Cronograma M06 (cinco horizontes LC 214/2025) — bloco partilhado na vista unificada por empresa.
 */
export function DiagnosticoCronogramaM06Card({ cronograma }: Props) {
  if (!cronograma.length) return null;

  return (
    <Card className="mb-10" id="empresa-cronograma-m06">
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
            {cronograma.map((linha) => (
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
            {cronograma.map((linha, idx) => (
              <li
                key={linha.fase}
                className="relative scroll-mt-4 rounded-md outline-none focus-within:ring-2 focus-within:ring-primary/50 focus-within:ring-offset-2 focus-within:ring-offset-background"
              >
                <span
                  className="absolute -left-[26px] sm:-left-[30px] top-1 flex h-4 w-4 rounded-full bg-primary shadow-md ring-[3px] ring-background motion-reduce:shadow-none"
                  aria-hidden
                />
                <span className="sr-only">
                  Fase {idx + 1} de {cronograma.length}
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
  );
}
