"use client";

import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";
import { MessageSquare, ListChecks } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { buildPlanoAcaoFichaHref } from "@/lib/dashboard/plano_acao_ficha_urls";
import { COLUNAS_KANBAN } from "@/lib/api/plano_acao_kanban";
import {
  chavesQuadroIniciais,
  formatarMetaPrazoPtBr,
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
  return custom || card.texto_acao;
}

export function PlanoAcaoKanbanBoard({
  cnpj14,
  razaoSocial,
  diagnosticoId,
  detalhe,
  cardsPorPlanoId,
  editavel,
}: Props) {
  const router = useRouter();
  const [mostrarArquivados, setMostrarArquivados] = useState(false);

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

  return (
    <section className="space-y-4" aria-labelledby="empresa-kanban-plano-titulo">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h3
            id="empresa-kanban-plano-titulo"
            className="text-base font-semibold tracking-tight scroll-mt-24"
          >
            Execução do plano — Kanban
          </h3>
          <p className="text-sm text-muted-foreground mt-1 max-w-3xl">
            Clique num card para abrir a ficha unificada (planejamento + status operacional). A grelha
            acima mostra os mesmos dados em formato tabular.
          </p>
        </div>
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => setMostrarArquivados((v) => !v)}
        >
          {mostrarArquivados ? "Ocultar arquivados" : "Ver arquivados"}
        </Button>
      </div>

      {cards.length === 0 ? (
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
    </section>
  );
}
