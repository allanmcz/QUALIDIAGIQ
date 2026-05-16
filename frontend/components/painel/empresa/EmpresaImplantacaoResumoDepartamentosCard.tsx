"use client";

import { useMemo } from "react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { resumoAtividadesImplantacaoPorFrente } from "@/lib/painel/quadro_implantacao_utils";
import type { DiagnosticoDetalheApi } from "@/types/diagnostico_detalhe";

/** Resumo do quadro único por empresa (âncora técnica no baseline canónico). */
export function EmpresaImplantacaoResumoDepartamentosCard({ data }: { data: DiagnosticoDetalheApi }) {
  const rows = useMemo(
    () => resumoAtividadesImplantacaoPorFrente(data.checklist, data.quadro_implantacao_anotacoes),
    [data.checklist, data.quadro_implantacao_anotacoes],
  );

  if (!rows.length) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Atividades do quadro — por frente</CardTitle>
        <p className="text-sm font-normal text-muted-foreground">
          Consolidação do quadro de implantação ao nível da empresa.{" "}
          <span className="font-medium text-foreground">Finalizada</span> conta quando há meta de prazo ISO e pelo
          menos uma nota do consultor; o restante fica como <span className="font-medium text-foreground">pendente</span>.
        </p>
      </CardHeader>
      <CardContent>
        <ul className="space-y-3 text-sm" aria-label="Resumo por frente">
          {rows.map((r) => (
            <li
              key={r.frente}
              className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1 rounded-md border px-3 py-2 bg-muted/10"
            >
              <span className="font-medium text-foreground">{r.frente}</span>
              <span className="tabular-nums text-muted-foreground">
                total {r.total}
                <span className="mx-1 text-border">·</span>
                pendentes {r.pendentes}
                <span className="mx-1 text-border">·</span>
                finalizadas {r.finalizadas}
              </span>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}
