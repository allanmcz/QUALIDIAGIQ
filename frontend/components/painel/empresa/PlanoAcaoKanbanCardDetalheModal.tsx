"use client";

import { useCallback, useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  adicionarComentarioKanban,
  arquivarKanbanCard,
  atualizarEstadoKanbanCard,
  listarComentariosKanban,
} from "@/lib/api/plano_acao_kanban";
import type { AcaoChecklistDetalhe } from "@/types/diagnostico_detalhe";
import type {
  PlanoAcaoComentarioApi,
  PlanoAcaoKanbanCardApi,
  StatusExecucaoPlanoAcao,
} from "@/types/plano_acao_kanban";

type Props = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  diagnosticoId: string;
  card: PlanoAcaoKanbanCardApi | null;
  editavel: boolean;
  acaoChecklist?: AcaoChecklistDetalhe | null;
  onCardAtualizado: (card: PlanoAcaoKanbanCardApi) => void;
  onArquivado?: () => void;
};

export function PlanoAcaoKanbanCardDetalheModal({
  open,
  onOpenChange,
  diagnosticoId,
  card,
  editavel,
  acaoChecklist,
  onCardAtualizado,
  onArquivado,
}: Props) {
  const [status, setStatus] = useState<StatusExecucaoPlanoAcao>("pendente");
  const [responsavel, setResponsavel] = useState("");
  const [prazo, setPrazo] = useState("");
  const [bloqueio, setBloqueio] = useState("");
  const [descricaoOp, setDescricaoOp] = useState("");
  const [comentarios, setComentarios] = useState<PlanoAcaoComentarioApi[]>([]);
  const [novoComentario, setNovoComentario] = useState("");
  const [msg, setMsg] = useState<string | null>(null);
  const [salvando, setSalvando] = useState(false);

  useEffect(() => {
    if (!card) return;
    setStatus(card.status_execucao);
    setResponsavel(card.responsavel_operacional ?? "");
    setPrazo(card.prazo_operacional ?? "");
    setBloqueio(card.bloqueio_motivo ?? "");
    setDescricaoOp(card.descricao_operacional ?? "");
    setMsg(null);
    setNovoComentario("");
  }, [card]);

  const carregarComentarios = useCallback(async () => {
    if (!card) return;
    try {
      const itens = await listarComentariosKanban(diagnosticoId, card.plano_acao_id);
      setComentarios(itens);
    } catch {
      setComentarios([]);
    }
  }, [card, diagnosticoId]);

  useEffect(() => {
    if (open && card) void carregarComentarios();
  }, [open, card, carregarComentarios]);

  const salvarEstado = async () => {
    if (!card || !editavel) return;
    setSalvando(true);
    setMsg(null);
    try {
      const atualizado = await atualizarEstadoKanbanCard(diagnosticoId, card.plano_acao_id, {
        status_execucao: status,
        responsavel_operacional: responsavel.trim() || null,
        prazo_operacional: prazo.trim() || null,
        limpar_prazo: !prazo.trim(),
        bloqueio_motivo: status === "bloqueado" ? bloqueio.trim() || null : null,
        limpar_bloqueio: status !== "bloqueado",
        descricao_operacional: descricaoOp.trim() || null,
      });
      onCardAtualizado(atualizado);
      setMsg("Estado gravado.");
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Falha ao gravar.");
    } finally {
      setSalvando(false);
    }
  };

  const enviarComentario = async () => {
    if (!card || !editavel || !novoComentario.trim()) return;
    setSalvando(true);
    setMsg(null);
    try {
      await adicionarComentarioKanban(diagnosticoId, card.plano_acao_id, novoComentario.trim());
      setNovoComentario("");
      await carregarComentarios();
      onCardAtualizado({
        ...card,
        comentarios_total: card.comentarios_total + 1,
      });
      setMsg("Comentário registado.");
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Falha ao comentar.");
    } finally {
      setSalvando(false);
    }
  };

  const toggleArquivar = async () => {
    if (!card || !editavel) return;
    setSalvando(true);
    try {
      await arquivarKanbanCard(diagnosticoId, card.plano_acao_id, !card.arquivado);
      onArquivado?.();
      onOpenChange(false);
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Falha ao arquivar.");
    } finally {
      setSalvando(false);
    }
  };

  if (!card) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-left pr-8">
            <span className="text-muted-foreground font-normal tabular-nums mr-2">
              #{card.ordem_kanban + 1}
            </span>
            {card.texto_acao}
          </DialogTitle>
          <DialogDescription className="text-left">
            {card.frente_nome}
            {card.fase_pdca ? ` · PDCA ${card.fase_pdca}` : ""}
            {card.criticidade ? ` · ${card.criticidade}` : ""}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 text-sm">
          <div className="rounded-md border bg-muted/30 p-3 space-y-1">
            <p className="font-medium text-foreground">Texto original do motor</p>
            <p className="text-muted-foreground">{card.texto_acao}</p>
            {card.base_legal ? (
              <p className="text-xs text-muted-foreground">Base: {card.base_legal}</p>
            ) : null}
            {card.horizonte_planejado ? (
              <p className="text-xs">Horizonte: {card.horizonte_planejado}</p>
            ) : null}
            {card.responsavel_sugerido ? (
              <p className="text-xs">Responsável sugerido: {card.responsavel_sugerido}</p>
            ) : null}
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            <div className="space-y-1">
              <Label>Status operacional</Label>
              <Select
                value={status}
                onValueChange={(v) => setStatus(v as StatusExecucaoPlanoAcao)}
                disabled={!editavel}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="pendente">A iniciar</SelectItem>
                  <SelectItem value="em_andamento">Em andamento</SelectItem>
                  <SelectItem value="bloqueado">Bloqueado</SelectItem>
                  <SelectItem value="concluida">Concluído</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1">
              <Label>Responsável operacional</Label>
              <Input
                value={responsavel}
                onChange={(e) => setResponsavel(e.target.value)}
                disabled={!editavel}
                placeholder="Nome ou função"
              />
            </div>
            <div className="space-y-1">
              <Label>Prazo operacional</Label>
              <Input
                type="date"
                value={prazo}
                onChange={(e) => setPrazo(e.target.value)}
                disabled={!editavel}
              />
            </div>
            {status === "bloqueado" ? (
              <div className="space-y-1 sm:col-span-2">
                <Label>Motivo do bloqueio</Label>
                <textarea
                  className="flex min-h-[60px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  value={bloqueio}
                  onChange={(e) => setBloqueio(e.target.value)}
                  disabled={!editavel}
                  rows={2}
                />
              </div>
            ) : null}
            <div className="space-y-1 sm:col-span-2">
              <Label>Notas operacionais</Label>
              <textarea
                className="flex min-h-[60px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                value={descricaoOp}
                onChange={(e) => setDescricaoOp(e.target.value)}
                disabled={!editavel}
                rows={2}
              />
            </div>
          </div>

          {acaoChecklist?.subtarefas?.length ? (
            <div className="space-y-2">
              <p className="font-medium">Subtarefas ({acaoChecklist.subtarefas.length})</p>
              <ul className="list-disc pl-5 text-muted-foreground space-y-1">
                {acaoChecklist.subtarefas.map((s) => (
                  <li key={s.id}>
                    {s.titulo} — <span className="text-xs">{s.status}</span>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          <div className="space-y-2 border-t pt-3">
            <p className="font-medium">Comentários auditáveis</p>
            <ul className="space-y-2 max-h-40 overflow-y-auto">
              {comentarios.length === 0 ? (
                <li className="text-muted-foreground text-xs">Nenhum comentário ainda.</li>
              ) : (
                comentarios.map((c) => (
                  <li key={c.id} className="rounded border p-2 text-xs">
                    <span className="font-medium">{c.autor_label}</span>
                    <span className="text-muted-foreground ml-2">
                      {new Date(c.criado_em).toLocaleString("pt-BR")}
                    </span>
                    <p className="mt-1 whitespace-pre-wrap">{c.comentario}</p>
                  </li>
                ))
              )}
            </ul>
            {editavel ? (
              <div className="flex gap-2">
                <textarea
                  value={novoComentario}
                  onChange={(e) => setNovoComentario(e.target.value)}
                  placeholder="Novo comentário (imutável após gravar)"
                  rows={2}
                  className="flex min-h-[60px] flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm"
                />
                <Button type="button" variant="secondary" onClick={() => void enviarComentario()} disabled={salvando}>
                  Enviar
                </Button>
              </div>
            ) : null}
          </div>

          {msg ? <p className="text-sm text-muted-foreground" role="status">{msg}</p> : null}
        </div>

        <DialogFooter className="flex-col sm:flex-row gap-2">
          {editavel ? (
            <>
              <Button type="button" variant="outline" onClick={() => void toggleArquivar()} disabled={salvando}>
                {card.arquivado ? "Restaurar" : "Arquivar"}
              </Button>
              <Button type="button" onClick={() => void salvarEstado()} disabled={salvando}>
                Gravar estado
              </Button>
            </>
          ) : (
            <Button type="button" variant="secondary" onClick={() => onOpenChange(false)}>
              Fechar
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
