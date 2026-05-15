import type { DiagnosticoDetalheApi } from "@/types/diagnostico_detalhe";

export type AcaoChecklistQuadro = {
  descricao: string;
  responsavel: string;
  prazo: string;
  criticidade: string;
  base_legal?: string | null;
  prioridade?: number;
  plano_acao_id?: string;
  chave_quadro_legado?: string;
};

export type FrenteChecklistQuadro = { nome: string; acoes: AcaoChecklistQuadro[] };

export type QuadroEdicaoAcao = {
  prazo_meta: string;
  comentarios: string[];
  descricao_personalizada: string;
};

export function defaultQuadroEdicaoAcao(): QuadroEdicaoAcao {
  return {
    prazo_meta: "",
    comentarios: [],
    descricao_personalizada: "",
  };
}

export function formatarMetaPrazoPtBr(iso: string): string {
  const s = (iso || "").trim();
  if (s.length !== 10 || s[4] !== "-" || s[7] !== "-") return s || "—";
  const [y, m, d] = s.split("-");
  return `${d}/${m}/${y}`;
}

export function chaveQuadroParaAcao(acao: AcaoChecklistQuadro, i: number, j: number): string {
  const pid = (acao.plano_acao_id || "").trim();
  if (pid.length >= 32 && /^[0-9a-f-]+$/i.test(pid)) {
    return pid;
  }
  return `f${i}_a${j}`;
}

export function chavesQuadroIniciais(
  checklist: FrenteChecklistQuadro[] | null | undefined,
  persistido: DiagnosticoDetalheApi["quadro_implantacao_anotacoes"],
): Record<string, QuadroEdicaoAcao> {
  const out: Record<string, QuadroEdicaoAcao> = {};
  if (!checklist) return out;
  checklist.forEach((f, i) => {
    f.acoes.forEach((acao, j) => {
      const k = chaveQuadroParaAcao(acao, i, j);
      const p = persistido?.[k] ?? persistido?.[`f${i}_a${j}`];
      const fromList = Array.isArray(p?.comentarios)
        ? p!.comentarios!.filter((x): x is string => typeof x === "string")
        : [];
      const legacy =
        typeof p?.comentario === "string" && p.comentario.trim() ? [p.comentario.trim()] : [];
      const comentarios = fromList.length > 0 ? [...fromList] : legacy;
      out[k] = {
        prazo_meta: typeof p?.prazo_meta === "string" ? p.prazo_meta : "",
        comentarios,
        descricao_personalizada:
          typeof p?.descricao_personalizada === "string" ? p.descricao_personalizada.trim() : "",
      };
    });
  });
  return out;
}

/** Linhas achatadas para a grelha (frente + ação + chave). */
export function linhasQuadroGrid(
  checklist: FrenteChecklistQuadro[] | null | undefined,
): Array<{ frente: string; acao: AcaoChecklistQuadro; i: number; j: number; qk: string }> {
  if (!checklist) return [];
  const rows: Array<{ frente: string; acao: AcaoChecklistQuadro; i: number; j: number; qk: string }> = [];
  checklist.forEach((f, i) => {
    f.acoes.forEach((acao, j) => {
      rows.push({ frente: f.nome, acao, i, j, qk: chaveQuadroParaAcao(acao, i, j) });
    });
  });
  return rows;
}
