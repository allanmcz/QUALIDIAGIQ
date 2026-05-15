"use client";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { DiagnosticoDetalheApi } from "@/types/diagnostico_detalhe";

type Props = {
  matriz: DiagnosticoDetalheApi["matriz_impacto"];
  className?: string;
  id?: string;
};

/** Matriz M04 — departamento × impacto × criticidade (somente leitura). */
export function MatrizImpactoDepartamentoCard({ matriz, className, id }: Props) {
  if (!matriz?.length) return null;

  return (
    <Card id={id} className={className ?? "scroll-mt-24"}>
      <CardHeader>
        <CardTitle className="text-base">Matriz de impacto por departamento</CardTitle>
      </CardHeader>
      <CardContent className="overflow-x-auto">
        <table className="w-full text-sm border-collapse min-w-[640px]">
          <thead>
            <tr className="border-b">
              <th scope="col" className="text-left py-2 pr-4">
                Departamento
              </th>
              <th scope="col" className="text-left py-2 pr-4">
                Impacto
              </th>
              <th scope="col" className="text-left py-2 pr-4">
                Criticidade
              </th>
              <th scope="col" className="text-left py-2">
                Base legal
              </th>
            </tr>
          </thead>
          <tbody>
            {matriz.map((m) => (
              <tr key={m.departamento} className="border-b border-muted">
                <td className="py-2 pr-4 font-medium align-top">{m.departamento}</td>
                <td className="py-2 pr-4 align-top">{m.impacto_resumo}</td>
                <td className="py-2 pr-4 align-top">
                  <Badge variant={m.criticidade === "Crítica" ? "destructive" : "secondary"}>
                    {m.criticidade}
                  </Badge>
                </td>
                <td className="py-2 text-muted-foreground text-xs align-top">{m.base_legal ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </CardContent>
    </Card>
  );
}
