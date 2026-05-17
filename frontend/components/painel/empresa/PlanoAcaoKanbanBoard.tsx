"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { MessageSquare, ListChecks } from "lucide-react";

import { PlanoAcaoKanbanCardDetalheModal } from "@/components/painel/empresa/PlanoAcaoKanbanCardDetalheModal";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { COLUNAS_KANBAN, buscarKanbanPlanoAcao } from "@/lib/api/plano_acao_kanban";
import { cn } from "@/lib/utils";
import { temSessaoPainelParaApiCliente } from "@/lib/api/config";
import type { DiagnosticoDetalheApi, AcaoChecklistDetalhe } from "@/types/diagnostico_detalhe";
import type { PlanoAcaoKanbanCardApi } from "@/types/plano_acao_kanban";

type Props = {
  diagnosticoId: string;
  detalhe: DiagnosticoDetalheApi;
  editavel: boolean;
};

function mapAcoesPorPlanoId(detalhe: DiagnosticoDetalheApi): Map<string, AcaoChecklistDetalhe> {
  const map = new Map<string, AcaoChecklistDetalhe>();
  for (const frente of detalhe.checklist ?? []) {
    for (const acao of frente.acoes) {
      if (acao.plano_acao_id) map.set(acao.plano_acao_id, acao);
    }
  }
  return map;
}

export function PlanoAcaoKanbanBoard({ diagnosticoId, detalhe, editavel }: Props) {
  const [cards, setCards] = useState<PlanoAcaoKanbanCardApi[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);
  const [cardDetalhe, setCardDetalhe] = useState<PlanoAcaoKanbanCardApi | null>(null);
  const [modalAberto, setModalAberto] = useState(false);
  const [mostrarArquivados, setMostrarArquivados] = useState(false);

  const acoesPorId = useMemo(() => mapAcoesPorPlanoId(detalhe), [detalhe]);

  const recarregar = useCallback(async () => {
    if (!temSessaoPainelParaApiCliente() || detalhe.status !== "finalizado") {
      setCards([]);
      setCarregando(false);
      return;
    }
    setCarregando(true);
    setErro(null);
    try {
      const board = await buscarKanbanPlanoAcao(diagnosticoId, {
        incluirArquivados: mostrarArquivados,
      });
      setCards(board?.cards ?? []);
    } catch (e) {
      setErro(e instanceof Error ? e.message : "Não foi possível carregar o Kanban.");
      setCards([]);
    } finally {
      setCarregando(false);
    }
  }, [diagnosticoId, detalhe.status, mostrarArquivados]);

  useEffect(() => {
    void recarregar();
  }, [recarregar]);

  const cardsPorColuna = useMemo(() => {
    const grupos: Record<string, PlanoAcaoKanbanCardApi[]> = {};
    for (const col of COLUNAS_KANBAN) grupos[col.status] = [];
    for (const c of cards) {
      const lista = grupos[c.status_execucao];
      if (lista) lista.push(c);
    }
    return grupos;
  }, [cards]);

  const abrirDetalhe = (card: PlanoAcaoKanbanCardApi) => {
    setCardDetalhe(card);
    setModalAberto(true);
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
            Acompanhamento operacional sobre as ações materializadas (status, responsável, prazo e
            comentários auditáveis). A grelha acima mantém o quadro único por empresa; aqui você move a
            execução.
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

      {carregando ? (
        <p className="text-sm text-muted-foreground" role="status">
          A carregar Kanban…
        </p>
      ) : null}
      {erro ? (
        <p className="text-sm text-destructive" role="alert">
          {erro}
        </p>
      ) : null}

      {!carregando && !erro && cards.length === 0 ? (
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
                  onClick={() => abrirDetalhe(card)}
                >
                  <CardContent className="p-3 space-y-2">
                    <div className="flex items-start gap-2">
                      <Badge variant="outline" className="text-[10px] tabular-nums shrink-0">
                        #{card.ordem_kanban + 1}
                      </Badge>
                      <p className="text-sm font-medium leading-snug line-clamp-3 flex-1 min-w-0">
                        {card.texto_acao}
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
                      <span>{card.prazo_operacional ?? "—"}</span>
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

      <PlanoAcaoKanbanCardDetalheModal
        open={modalAberto}
        onOpenChange={setModalAberto}
        diagnosticoId={diagnosticoId}
        card={cardDetalhe}
        editavel={editavel}
        acaoChecklist={cardDetalhe ? acoesPorId.get(cardDetalhe.plano_acao_id) : null}
        onCardAtualizado={(c) => {
          setCards((prev) => prev.map((x) => (x.plano_acao_id === c.plano_acao_id ? c : x)));
          setCardDetalhe(c);
        }}
        onArquivado={() => void recarregar()}
      />
    </section>
  );
}
