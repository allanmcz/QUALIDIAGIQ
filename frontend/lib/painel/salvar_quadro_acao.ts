import { cabecalhosAuthPainelOpcional, getApiUrlForFetch } from "@/lib/api/config";
import { encerrarSessaoPainelSe401 } from "@/lib/auth/painel_session";
import type { QuadroEdicaoAcao } from "@/lib/painel/quadro_implantacao_utils";
import type { DiagnosticoDetalheApi } from "@/types/diagnostico_detalhe";

export type SalvarQuadroAcaoResult =
  | { ok: true; detalhe: DiagnosticoDetalheApi }
  | { ok: false; status: number; mensagem: string; conflitoVersao?: boolean };

/**
 * PATCH `quadro_implantacao_anotacoes` para uma chave (plano_acao_id ou f{i}_a{j}).
 */
export async function salvarQuadroAcao(
  diagnosticoId: string,
  chaveQuadro: string,
  edicao: QuadroEdicaoAcao,
  versaoOtimista: number,
): Promise<SalvarQuadroAcaoResult> {
  const body = {
    [chaveQuadro]: {
      prazo_meta: edicao.prazo_meta.trim(),
      comentarios: edicao.comentarios.map((s) => s.trim()).filter(Boolean),
      descricao_personalizada: (edicao.descricao_personalizada ?? "").trim(),
    },
  };

  const base = getApiUrlForFetch().replace(/\/$/, "");
  const res = await fetch(`${base}/diagnosticos/${diagnosticoId}/quadro-implantacao-anotacoes`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
      ...cabecalhosAuthPainelOpcional(),
      "If-Match": String(versaoOtimista),
    },
    credentials: "include",
    body: JSON.stringify({ quadro_implantacao_anotacoes: body }),
  });

  if (encerrarSessaoPainelSe401(res.status)) {
    return { ok: false, status: 401, mensagem: "Sessão expirada." };
  }
  if (res.ok) {
    const detalhe = (await res.json()) as DiagnosticoDetalheApi;
    return { ok: true, detalhe };
  }
  if (res.status === 412) {
    return {
      ok: false,
      status: 412,
      mensagem: "Conflito de versão — recarregue e tente novamente.",
      conflitoVersao: true,
    };
  }
  const t = await res.text();
  return {
    ok: false,
    status: res.status,
    mensagem: `Não foi possível gravar o quadro (${res.status}): ${t.slice(0, 160)}`,
  };
}
