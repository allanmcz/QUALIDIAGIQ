/**
 * Contrato alinhado a GET /diagnosticos/{id} — usado no detalhe e na expansão da grelha por empresa.
 */

import type { ExplicacaoScoreLlmHttp } from "@/lib/api/explicacao_score_llm";

export type AcaoChecklistDetalhe = {
  descricao: string;
  responsavel: string;
  prazo: string;
  criticidade: string;
  base_legal?: string | null;
  prioridade?: number;
  /** Sequência global do plano materializado (0 = primeira ação). */
  ordem_exibicao?: number;
  plano_acao_id?: string;
  chave_quadro_legado?: string;
  subtarefas?: Array<{
    id: string;
    titulo: string;
    status: string;
    prazo?: string | null;
    comentarios?: string | null;
    ordem: number;
  }>;
};

export type FrenteChecklistDetalhe = { nome: string; acoes: AcaoChecklistDetalhe[] };

export type QuadroItemPersistidoApi = {
  prazo_meta?: string;
  comentarios?: string[];
  comentario?: string;
  descricao_personalizada?: string;
};

export type DiagnosticoDetalheApi = {
  id: string;
  empresa_razao_social: string;
  empresa_cnpj?: string;
  /** Snapshot empresa — pré-preenchimento wizard «novo ciclo». */
  empresa_porte?: string | null;
  empresa_regime?: string | null;
  empresa_cnae?: string | null;
  empresa_uf?: string | null;
  empresa_setor_macro?: string | null;
  criado_em?: string | null;
  finalizado_em?: string | null;
  plano: string;
  status: string;
  relatorio_pdf_url: string | null;
  checklist: FrenteChecklistDetalhe[] | null;
  matriz_impacto: Array<{
    departamento: string;
    impacto_resumo: string;
    criticidade: string;
    base_legal?: string | null;
  }> | null;
  cronograma: Array<{
    fase: string;
    foco: string;
    referencia_normativa: string;
  }> | null;
  checklist_m12_autoconf: (number | boolean)[] | null;
  quadro_implantacao_anotacoes?: Record<string, QuadroItemPersistidoApi> | null;
  versao_otimista: number | null;
  versao_plano?: number;
  /** Estado administrativo persistido (`painel_estado_ciclo`). */
  painel_estado_ciclo?: string | null;
  score: {
    score_geral: { valor: number };
    score_por_dimensao: Record<string, { valor: number; peso_total_aplicado: number }>;
  } | null;
  /** Última narrativa POST explicacao-score-llm (JSONB). */
  explicacao_score_llm?: ExplicacaoScoreLlmHttp | null;
};
