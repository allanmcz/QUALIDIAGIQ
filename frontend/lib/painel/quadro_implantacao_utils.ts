import type { DiagnosticoDetalheApi } from "@/types/diagnostico_detalhe";

export type AcaoChecklistQuadro = {
  descricao: string;
  responsavel: string;
  prazo: string;
  criticidade: string;
  base_legal?: string | null;
  prioridade?: number;
  ordem_exibicao?: number;
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

/** Número humano da sequência (1 = primeira ação do plano). */
export function rotuloSequenciaAcao(
  ordemExibicao: number | null | undefined,
  indiceFallback: number,
): number {
  if (typeof ordemExibicao === "number" && Number.isFinite(ordemExibicao)) {
    return ordemExibicao + 1;
  }
  return indiceFallback + 1;
}

export function formatarMetaPrazoPtBr(iso: string): string {
  const s = (iso || "").trim();
  if (s.length !== 10 || s[4] !== "-" || s[7] !== "-") return s || "—";
  const [y, m, d] = s.split("-");
  return `${d}/${m}/${y}`;
}

export function chaveQuadroParaAcao(acao: AcaoChecklistQuadro, i: number, j: number): string {
  const pid = (acao.plano_acao_id || "").trim();
  if (ehChaveQuadroUuid(pid)) {
    return pid;
  }
  const legado = (acao.chave_quadro_legado || "").trim();
  if (legado) return legado;
  return `f${i}_a${j}`;
}

/** Chave persistida no PATCH do quadro — UUID do plano ou legado ``f{i}_a{j}``. */
export function ehChaveQuadroUuid(chave: string): boolean {
  const v = chave.trim();
  return v.length >= 32 && /^[0-9a-f-]+$/i.test(v);
}

/**
 * Resolve a chave usada em ``quadro_implantacao_anotacoes`` ao gravar a ficha unificada.
 * Evita retorno silencioso quando o checklist HTTP ainda não traz ``plano_acao_id``.
 */
export function resolverChaveQuadroSalvar(opts: {
  planoAcaoId: string;
  chaveDeAcaoCtx?: string | null;
  chaveQuadroLegado?: string | null;
}): string | null {
  const ctx = opts.chaveDeAcaoCtx?.trim();
  if (ctx) return ctx;
  const pid = opts.planoAcaoId.trim();
  if (ehChaveQuadroUuid(pid)) return pid;
  const leg = opts.chaveQuadroLegado?.trim();
  return leg || null;
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
): Array<{
  frente: string;
  acao: AcaoChecklistQuadro;
  i: number;
  j: number;
  qk: string;
  sequencia: number;
}> {
  if (!checklist) return [];
  const rows: Array<{
    frente: string;
    acao: AcaoChecklistQuadro;
    i: number;
    j: number;
    qk: string;
    sequencia: number;
  }> = [];
  let indiceGlobal = 0;
  checklist.forEach((f, i) => {
    f.acoes.forEach((acao, j) => {
      rows.push({
        frente: f.nome,
        acao,
        i,
        j,
        qk: chaveQuadroParaAcao(acao, i, j),
        sequencia: rotuloSequenciaAcao(acao.ordem_exibicao, indiceGlobal),
      });
      indiceGlobal += 1;
    });
  });
  return rows;
}

/** Por frente («departamento» do quadro): totais para o cartão consolidado ao nível da empresa. */
export type ResumoAtividadesImplantacaoFrente = {
  frente: string;
  total: number;
  finalizadas: number;
  pendentes: number;
};

/** Uma linha conta como finalizada com meta de prazo e pelo menos uma nota (comentário) gravada pelo consultor. */
export function resumoAtividadesImplantacaoPorFrente(
  checklist: FrenteChecklistQuadro[] | null | undefined,
  persistido: DiagnosticoDetalheApi["quadro_implantacao_anotacoes"],
): ResumoAtividadesImplantacaoFrente[] {
  const inicial = chavesQuadroIniciais(checklist, persistido ?? null);
  const linhas = linhasQuadroGrid(checklist);
  const porNome = new Map<string, { total: number; finalizadas: number }>();
  for (const L of linhas) {
    const cur = porNome.get(L.frente) ?? { total: 0, finalizadas: 0 };
    cur.total += 1;
    const ed = inicial[L.qk];
    const prazoOk = !!(ed?.prazo_meta && String(ed.prazo_meta).trim());
    const comenta =
      Array.isArray(ed?.comentarios) &&
      ed.comentarios.some((c) => typeof c === "string" && c.trim().length > 0);
    if (prazoOk && comenta) cur.finalizadas += 1;
    porNome.set(L.frente, cur);
  }
  const out: ResumoAtividadesImplantacaoFrente[] = [];
  porNome.forEach((v, frente) => {
    out.push({
      frente,
      total: v.total,
      finalizadas: v.finalizadas,
      pendentes: Math.max(0, v.total - v.finalizadas),
    });
  });
  out.sort((a, b) => a.frente.localeCompare(b.frente, "pt-BR"));
  return out;
}
