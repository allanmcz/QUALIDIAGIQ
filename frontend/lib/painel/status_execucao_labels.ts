import type { StatusExecucaoPlanoAcao } from "@/types/plano_acao_kanban";

export const STATUS_EXECUCAO_LABEL: Record<StatusExecucaoPlanoAcao, string> = {
  pendente: "A iniciar",
  em_andamento: "Em andamento",
  bloqueado: "Bloqueado",
  concluida: "Concluído",
};

export function labelStatusExecucao(status: string | null | undefined): string {
  if (!status) return "—";
  return STATUS_EXECUCAO_LABEL[status as StatusExecucaoPlanoAcao] ?? status;
}
