import {
  cabecalhosAuthPainelOpcional,
  getApiUrlForFetch,
} from "@/lib/api/config";
import { encerrarSessaoPainelSe401 } from "@/lib/auth/painel_session";
import type {
  PlanoAcaoComentarioApi,
  PlanoAcaoKanbanBoardApi,
  PlanoAcaoKanbanCardApi,
  StatusExecucaoPlanoAcao,
} from "@/types/plano_acao_kanban";

function novaIdempotencyKey(): string {
  return typeof crypto !== "undefined" && crypto.randomUUID
    ? crypto.randomUUID()
    : `kanban-${Date.now()}`;
}

async function parseErro(res: Response): Promise<string> {
  try {
    const j = (await res.json()) as { detail?: string | { msg?: string }[] };
    if (typeof j.detail === "string") return j.detail;
    if (Array.isArray(j.detail) && j.detail[0]?.msg) return j.detail[0].msg;
  } catch {
    /* ignore */
  }
  if (res.status === 503) {
    return "Kanban indisponível no servidor — confirme `make migrate` (migração 0051) e reinicie a API.";
  }
  return `Erro HTTP ${res.status}`;
}

export async function buscarKanbanPlanoAcao(
  diagnosticoId: string,
  opts?: { incluirArquivados?: boolean },
): Promise<PlanoAcaoKanbanBoardApi | null> {
  const base = getApiUrlForFetch().replace(/\/$/, "");
  const qs = opts?.incluirArquivados ? "?incluir_arquivados=true" : "";
  const res = await fetch(`${base}/diagnosticos/${diagnosticoId}/plano-acao/kanban${qs}`, {
    headers: { Accept: "application/json", ...cabecalhosAuthPainelOpcional() },
    cache: "no-store",
    credentials: "include",
  });
  if (encerrarSessaoPainelSe401(res.status)) return null;
  if (!res.ok) throw new Error(await parseErro(res));
  return (await res.json()) as PlanoAcaoKanbanBoardApi;
}

export async function atualizarEstadoKanbanCard(
  diagnosticoId: string,
  planoAcaoId: string,
  body: {
    status_execucao?: StatusExecucaoPlanoAcao;
    responsavel_operacional?: string | null;
    prazo_operacional?: string | null;
    limpar_prazo?: boolean;
    bloqueio_motivo?: string | null;
    limpar_bloqueio?: boolean;
    descricao_operacional?: string | null;
  },
): Promise<PlanoAcaoKanbanCardApi> {
  const base = getApiUrlForFetch().replace(/\/$/, "");
  const res = await fetch(
    `${base}/diagnosticos/${diagnosticoId}/plano-acao/${planoAcaoId}/estado-operacional`,
    {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
        ...cabecalhosAuthPainelOpcional(),
      },
      credentials: "include",
      body: JSON.stringify(body),
    },
  );
  if (encerrarSessaoPainelSe401(res.status)) throw new Error("Sessão encerrada");
  if (!res.ok) throw new Error(await parseErro(res));
  return (await res.json()) as PlanoAcaoKanbanCardApi;
}

export async function listarComentariosKanban(
  diagnosticoId: string,
  planoAcaoId: string,
): Promise<PlanoAcaoComentarioApi[]> {
  const base = getApiUrlForFetch().replace(/\/$/, "");
  const res = await fetch(
    `${base}/diagnosticos/${diagnosticoId}/plano-acao/${planoAcaoId}/comentarios`,
    {
      headers: { Accept: "application/json", ...cabecalhosAuthPainelOpcional() },
      cache: "no-store",
      credentials: "include",
    },
  );
  if (encerrarSessaoPainelSe401(res.status)) return [];
  if (!res.ok) throw new Error(await parseErro(res));
  const json = (await res.json()) as { itens: PlanoAcaoComentarioApi[] };
  return json.itens ?? [];
}

export async function adicionarComentarioKanban(
  diagnosticoId: string,
  planoAcaoId: string,
  comentario: string,
): Promise<PlanoAcaoComentarioApi> {
  const base = getApiUrlForFetch().replace(/\/$/, "");
  const res = await fetch(
    `${base}/diagnosticos/${diagnosticoId}/plano-acao/${planoAcaoId}/comentarios`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
        "Idempotency-Key": novaIdempotencyKey(),
        ...cabecalhosAuthPainelOpcional(),
      },
      credentials: "include",
      body: JSON.stringify({ comentario }),
    },
  );
  if (encerrarSessaoPainelSe401(res.status)) throw new Error("Sessão encerrada");
  if (!res.ok) throw new Error(await parseErro(res));
  return (await res.json()) as PlanoAcaoComentarioApi;
}

export async function arquivarKanbanCard(
  diagnosticoId: string,
  planoAcaoId: string,
  arquivado: boolean,
): Promise<PlanoAcaoKanbanCardApi> {
  const base = getApiUrlForFetch().replace(/\/$/, "");
  const res = await fetch(
    `${base}/diagnosticos/${diagnosticoId}/plano-acao/${planoAcaoId}/arquivar`,
    {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
        ...cabecalhosAuthPainelOpcional(),
      },
      credentials: "include",
      body: JSON.stringify({ arquivado }),
    },
  );
  if (encerrarSessaoPainelSe401(res.status)) throw new Error("Sessão encerrada");
  if (!res.ok) throw new Error(await parseErro(res));
  return (await res.json()) as PlanoAcaoKanbanCardApi;
}

export const COLUNAS_KANBAN: {
  status: StatusExecucaoPlanoAcao;
  titulo: string;
}[] = [
  { status: "pendente", titulo: "A iniciar" },
  { status: "em_andamento", titulo: "Em andamento" },
  { status: "bloqueado", titulo: "Bloqueado" },
  { status: "concluida", titulo: "Concluído" },
];
