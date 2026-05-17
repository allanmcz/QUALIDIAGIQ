"use client";

import { useCallback, useEffect, useState } from "react";
import { FileDown, Loader2 } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  abrirPdfComparacaoQuestionario,
  fetchCompararQuestionario,
  type ComparacaoQuestionarioApi,
} from "@/lib/api/questionario_painel";
import { cn } from "@/lib/utils";

type Props = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  diagnosticoIds: string[];
  onLimparSelecao?: () => void;
};

function rotuloColuna(d: ComparacaoQuestionarioApi["diagnosticos"][number]): string {
  const data = d.finalizado_em
    ? new Date(d.finalizado_em).toLocaleDateString("pt-BR", {
        day: "2-digit",
        month: "short",
        year: "2-digit",
      })
    : "—";
  const n = d.numero_interno_grupo != null ? `#${d.numero_interno_grupo}` : d.diagnostico_id.slice(0, 8);
  const score = d.score_geral != null ? `${d.score_geral.toFixed(1)}` : "—";
  return `${n} · ${data} · ${score}`;
}

function celulasIguais(
  linha: ComparacaoQuestionarioApi["linhas"][number],
  diagIds: string[],
): boolean {
  const vals = diagIds.map((id) => linha.valores_por_diagnostico[id]?.valor_exibicao ?? "");
  return vals.length > 1 && vals.every((v) => v === vals[0]);
}

export function EmpresaComparacaoQuestionarioDialog({
  open,
  onOpenChange,
  diagnosticoIds,
  onLimparSelecao,
}: Props) {
  const [dados, setDados] = useState<ComparacaoQuestionarioApi | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(false);
  const [exportandoPdf, setExportandoPdf] = useState(false);

  const carregar = useCallback(async () => {
    if (diagnosticoIds.length < 2) return;
    setCarregando(true);
    setErro(null);
    try {
      const r = await fetchCompararQuestionario(diagnosticoIds);
      setDados(r);
    } catch (e) {
      setDados(null);
      setErro(e instanceof Error ? e.message : "Falha ao comparar questionários.");
    } finally {
      setCarregando(false);
    }
  }, [diagnosticoIds]);

  useEffect(() => {
    if (!open) return;
    void carregar();
  }, [open, carregar]);

  const diagIds = dados?.diagnosticos.map((d) => d.diagnostico_id) ?? [];

  const exportarPdf = useCallback(async () => {
    if (diagnosticoIds.length < 2) return;
    setExportandoPdf(true);
    setErro(null);
    try {
      await abrirPdfComparacaoQuestionario(diagnosticoIds);
    } catch (e) {
      setErro(e instanceof Error ? e.message : "Falha ao gerar PDF da comparação.");
    } finally {
      setExportandoPdf(false);
    }
  }, [diagnosticoIds]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-[min(96vw,72rem)] max-h-[90vh] flex flex-col">
        <DialogHeader>
          <DialogTitle>Comparar questionário entre ciclos</DialogTitle>
          <DialogDescription>
            {dados?.empresa_razao_social ?? "Empresa"} — alinhamento por código de pergunta (
            <span className="font-mono text-xs">Q-…</span>). Destaque quando a resposta mudou entre
            ciclos.
          </DialogDescription>
        </DialogHeader>

        {carregando ? (
          <div className="flex items-center justify-center gap-2 py-12 text-muted-foreground">
            <Loader2 className="h-5 w-5 animate-spin" aria-hidden />
            Carregando comparação…
          </div>
        ) : null}

        {erro ? (
          <p className="text-sm text-destructive py-4" role="alert">
            {erro}
          </p>
        ) : null}

        {dados && !carregando && !erro ? (
          <div className="flex-1 overflow-auto border rounded-lg">
            <table className="w-full text-sm border-collapse min-w-[40rem]">
              <thead className="sticky top-0 bg-muted/90 backdrop-blur z-10">
                <tr className="border-b">
                  <th className="text-left p-2 font-semibold w-24">Código</th>
                  <th className="text-left p-2 font-semibold min-w-[14rem]">Pergunta</th>
                  {dados.diagnosticos.map((d) => (
                    <th key={d.diagnostico_id} className="text-left p-2 font-semibold min-w-[8rem]">
                      <span className="block text-[10px] font-normal text-muted-foreground leading-tight">
                        {rotuloColuna(d)}
                      </span>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {dados.linhas.map((linha) => {
                  const iguais = celulasIguais(linha, diagIds);
                  return (
                    <tr
                      key={linha.pergunta_codigo}
                      className={cn(
                        "border-b border-muted/60 align-top",
                        !iguais && "bg-amber-500/5",
                      )}
                    >
                      <td className="p-2 font-mono text-xs">{linha.pergunta_codigo}</td>
                      <td className="p-2 text-xs leading-snug">
                        {linha.texto_pergunta}
                        {linha.base_legal ? (
                          <span className="block text-muted-foreground mt-0.5">{linha.base_legal}</span>
                        ) : null}
                      </td>
                      {diagIds.map((id) => {
                        const v = linha.valores_por_diagnostico[id];
                        return (
                          <td key={id} className="p-2 text-xs">
                            <span className="font-medium">{v?.valor_exibicao ?? "—"}</span>
                            {v?.excluida_calculo ? (
                              <Badge variant="outline" className="ml-1 text-[9px]">
                                fora cálculo
                              </Badge>
                            ) : null}
                          </td>
                        );
                      })}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : null}

        <DialogFooter className="gap-2 sm:gap-0 flex-wrap">
          {onLimparSelecao ? (
            <Button type="button" variant="ghost" onClick={onLimparSelecao}>
              Limpar seleção
            </Button>
          ) : null}
          <Button
            type="button"
            variant="secondary"
            disabled={!dados || exportandoPdf || diagnosticoIds.length < 2}
            onClick={() => void exportarPdf()}
          >
            {exportandoPdf ? (
              <Loader2 className="h-4 w-4 animate-spin mr-2" aria-hidden />
            ) : (
              <FileDown className="h-4 w-4 mr-2" aria-hidden />
            )}
            Exportar PDF
          </Button>
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
            Fechar
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
