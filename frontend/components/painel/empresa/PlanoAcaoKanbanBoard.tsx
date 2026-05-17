"use client";

import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { ChevronDown, ListChecks, MessageSquare } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { buildPlanoAcaoFichaHref } from "@/lib/dashboard/plano_acao_ficha_urls";
import { COLUNAS_KANBAN } from "@/lib/api/plano_acao_kanban";
import {
  chavesQuadroIniciais,
  formatarMetaPrazoPtBr,
  limparSufixoLacunaScoreAcao,
} from "@/lib/painel/quadro_implantacao_utils";
import { cn } from "@/lib/utils";
import type { DiagnosticoDetalheApi } from "@/types/diagnostico_detalhe";
import type { PlanoAcaoKanbanCardApi } from "@/types/plano_acao_kanban";

type Props = {
  cnpj14: string;
  razaoSocial?: string;
  diagnosticoId: string;
  detalhe: DiagnosticoDetalheApi;
  cardsPorPlanoId: Record<string, PlanoAcaoKanbanCardApi>;
  onKanbanAlterado?: () => void;
  editavel: boolean;
};

function tituloExibidoCard(card: PlanoAcaoKanbanCardApi, detalhe: DiagnosticoDetalheApi): string {
  const edits = chavesQuadroIniciais(detalhe.checklist, detalhe.quadro_implantacao_anotacoes);
  const custom = edits[card.plano_acao_id]?.descricao_personalizada?.trim();
  return custom || limparSufixoLacunaScoreAcao(card.texto_acao);
}

export function PlanoAcaoKanbanBoard({
  cnpj14,
  razaoSocial,
  diagnosticoId,
  detalhe,
  cardsPorPlanoId,
  onKanbanAlterado: _onKanbanAlterado,
  editavel: _editavel,
}: Props) {
  const router = useRouter();
  const [expandido, setExpandido] = useState(false);
  const [mostrarArquivados, setMostrarArquivados] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const hash = window.location.hash.replace(/^#/, "").trim();
    if (hash === "empresa-kanban-plano-titulo") setExpandido(true);
  }, []);

  const cards = useMemo(() => {
    const todos = Object.values(cardsPorPlanoId);
    return mostrarArquivados ? todos : todos.filter((c) => !c.arquivado);
  }, [cardsPorPlanoId, mostrarArquivados]);

  const cardsPorColuna = useMemo(() => {
    const grupos: Record<string, PlanoAcaoKanbanCardApi[]> = {};
    for (const col of COLUNAS_KANBAN) grupos[col.status] = [];
    for (const c of cards) {
      const lista = grupos[c.status_execucao];
      if (lista) lista.push(c);
    }
    return grupos;
  }, [cards]);

  const abrirFicha = (card: PlanoAcaoKanbanCardApi) => {
    router.push(
      buildPlanoAcaoFichaHref(cnpj14, card.plano_acao_id, {
        diagnosticoId,
        razaoSocial,
        hashVolta: "empresa-kanban-plano-titulo",
      }),
    );
  };

  if (detalhe.status !== "finalizado") {
    return (
      <p className="text-sm text-muted-foreground border rounded-md p-4 bg-muted/20">
        O Kanban de execução fica disponível após o diagnóstico de referência estar finalizado e o plano
        materializado na API.
      </p>
    );
  }

  const totalCards = cards.length;

  return (
    <section className="space-y-3" aria-labelledby="empresa-kanban-plano-titulo">
      <div
        id="empresa-kanban-plano-titulo"
        className="scroll-mt-24 rounded-lg border bg-muted/15"
      >
        <div className="flex flex-wrap items-start justify-between gap-3 p-4">
          <div className="min-w-0 space-y-2">
            <h3 className="text-base font-semibold tracking-tight">Execução do plano — Kanban</h3>
            {!expandido ? (
              <p className="text-sm text-muted-foreground max-w-3xl">
                Visão por colunas de status. A grelha acima já mostra o mesmo plano em formato tabular —{" "}
                <strong className="font-medium text-foreground">expanda</strong> para ver e abrir cards no
                Kanban.
              </p>
            ) : (
              <p className="text-sm text-muted-foreground max-w-3xl">
                Clique num card para abrir a ficha unificada (planejamento + status operacional).
              </p>
            )}
            {!expandido && totalCards > 0 ? (
              <div className="flex flex-wrap gap-2" aria-label="Resumo por coluna do Kanban">
                {COLUNAS_KANBAN.map((col) => {
                  const n = (cardsPorColuna[col.status] ?? []).length;
                  if (n === 0) return null;
                  return (
                    <Badge key={col.status} variant="secondary" className="text-xs font-normal">
                      {col.titulo}: {n}
                    </Badge>
                  );
                })}
                <Badge variant="outline" className="text-xs font-normal tabular-nums">
                  Total: {totalCards}
                </Badge>
              </div>
            ) : null}
          </div>
          <div className="flex flex-wrap items-center gap-2 shrink-0">
            {expandido ? (
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setMostrarArquivados((v) => !v)}
              >
                {mostrarArquivados ? "Ocultar arquivados" : "Ver arquivados"}
              </Button>
            ) : null}
            <Button
              type="button"
              variant={expandido ? "secondary" : "outline"}
              size="sm"
              className="gap-1.5"
              aria-expanded={expandido}
              aria-controls="empresa-kanban-plano-conteudo"
              onClick={() => setExpandido((v) => !v)}
            >
              <ChevronDown
                className={cn("h-4 w-4 shrink-0 transition-transform", expandido && "rotate-180")}
                aria-hidden
              />
              {expandido ? "Recolher" : "Expandir"}
            </Button>
          </div>
        </div>

        {expandido ? (
          <div id="empresa-kanban-plano-conteudo" className="space-y-4 border-t px-4 pb-4 pt-3">
            {totalCards === 0 ? (
              <p className="text-xs text-muted-foreground">
                Nenhum card no plano — confirme a materialização M07/M08 do ciclo de referência.
              </p>
            ) : null}

            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              {COLUNAS_KANBAN.map((col) => (
                <div key={col.status} className="space-y-2 min-w-0">
                  <div className="flex items-center justify-between gap-2 px-1">
                    <h4 className="text-sm font-semibold">{col.titulo}</h4>
                    <Badge variant="secondary" className="text-xs">
                      {(cardsPorColuna[col.status] ?? []).length}
                    </Badge>
                  </div>
                  <div className="space-y-2 min-h-[120px] rounded-lg border bg-muted/20 p-2">
                    {(cardsPorColuna[col.status] ?? []).map((card) => (
                      <Card
                        key={card.plano_acao_id}
                        className={cn(
                          "cursor-pointer shadow-sm hover:border-primary/40 transition-colors",
                          card.arquivado && "opacity-60",
                        )}
                        onClick={() => abrirFicha(card)}
                      >
                        <CardContent className="p-3 space-y-2">
                          <div className="flex items-start gap-2">
                            <Badge variant="outline" className="text-[10px] tabular-nums shrink-0">
                              #{card.ordem_kanban + 1}
                            </Badge>
                            <p className="text-sm font-medium leading-snug line-clamp-3 flex-1 min-w-0">
                              {tituloExibidoCard(card, detalhe)}
                            </p>
                          </div>
                          <p className="text-xs text-muted-foreground truncate">{card.frente_nome}</p>
                          <div className="flex flex-wrap gap-1">
                            {card.criticidade ? (
                              <Badge variant="outline" className="text-[10px]">
                                {card.criticidade}
                              </Badge>
                            ) : null}
                            {card.fase_pdca ? (
                              <Badge variant="secondary" className="text-[10px]">
                                {card.fase_pdca}
                              </Badge>
                            ) : null}
                          </div>
                          <div className="flex items-center justify-between text-xs text-muted-foreground">
                            <span className="truncate max-w-[55%]">
                              {card.responsavel_operacional || card.responsavel_sugerido || "—"}
                            </span>
                            <span>
                              {card.prazo_operacional
                                ? formatarMetaPrazoPtBr(card.prazo_operacional)
                                : "—"}
                            </span>
                          </div>
                          <div className="flex gap-3 text-muted-foreground">
                            <span className="inline-flex items-center gap-1 text-xs">
                              <MessageSquare className="h-3 w-3" aria-hidden />
                              {card.comentarios_total}
                            </span>
                            <span className="inline-flex items-center gap-1 text-xs">
                              <ListChecks className="h-3 w-3" aria-hidden />
                              {card.subtarefas_total}
                            </span>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : null}
      </div>
    </section>
  );
}
