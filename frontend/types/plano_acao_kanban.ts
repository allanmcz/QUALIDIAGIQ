/** Contrato GET/PATCH Kanban operacional do plano — `/diagnosticos/{id}/plano-acao/kanban`. */

export type StatusExecucaoPlanoAcao =
  | "pendente"
  | "em_andamento"
  | "bloqueado"
  | "concluida";

export type PlanoAcaoKanbanCardApi = {
  plano_acao_id: string;
  diagnostico_id: string;
  frente_indice: number;
  frente_nome: string;
  acao_indice: number;
  texto_acao: string;
  responsavel_sugerido?: string | null;
  prioridade_motor: number;
  criticidade?: string | null;
  base_legal?: string | null;
  fase_pdca?: string | null;
  horizonte_planejado?: string | null;
  chave_quadro_legado: string;
  status_execucao: StatusExecucaoPlanoAcao;
  responsavel_operacional?: string | null;
  prazo_operacional?: string | null;
  bloqueio_motivo?: string | null;
  descricao_operacional?: string | null;
  ordem_kanban: number;
  arquivado: boolean;
  comentarios_total: number;
  subtarefas_total: number;
};

export type PlanoAcaoKanbanBoardApi = {
  diagnostico_id: string;
  cards: PlanoAcaoKanbanCardApi[];
};

export type PlanoAcaoComentarioApi = {
  id: string;
  plano_acao_id: string;
  autor_label: string;
  autor_email?: string | null;
  comentario: string;
  sha256_payload: string;
  criado_em: string;
};
