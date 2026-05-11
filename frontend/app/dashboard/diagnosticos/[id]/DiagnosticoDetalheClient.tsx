"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  Bar,
  BarChart,
  Cell,
  PolarAngleAxis,
  PolarGrid,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { CalendarPlus, Pencil, Plus, RefreshCw, Trash2 } from "lucide-react";

import { PrivacidadeDiagnosticoCard } from "@/components/painel/PrivacidadeDiagnosticoCard";
import { RetificacaoDiagnosticoCard } from "@/components/painel/RetificacaoDiagnosticoCard";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
import { getAccessToken, getApiUrlForFetch, normalizarHrefRelatorioPdf } from "@/lib/api/config";
import { encerrarSessaoPainelSe401 } from "@/lib/auth/painel_session";
import {
  buildEmpresaDiagnosticosHref,
  buildWizardUrlNovaDiagnosticoEmpresa,
} from "@/lib/dashboard/empresa_diagnostico_urls";
import { clearPendingDiagnosticoFromStorage } from "@/lib/wizard/pending_diagnostico";
import { clearWizardDraft } from "@/lib/wizard/wizard_draft";

type AcaoChecklist = {
  descricao: string;
  responsavel: string;
  prazo: string;
  criticidade: string;
  base_legal?: string | null;
  prioridade?: number;
  /** UUID da linha materializada em BD — preferido para o quadro. */
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
type FrenteChecklist = { nome: string; acoes: AcaoChecklist[] };

type MatrizLinha = {
  departamento: string;
  impacto_resumo: string;
  criticidade: string;
  base_legal?: string | null;
};

type CronogramaFase = {
  fase: string;
  foco: string;
  referencia_normativa: string;
};

/** Item persistido no JSONB (lista nova + campo único legado). */
export type QuadroItemPersistidoApi = {
  comentario?: string;
  comentarios?: string[];
  prazo_meta?: string;
  /** Substitui a descrição canônica da ação no cartão do quadro (texto editável pelo consultor). */
  descricao_personalizada?: string;
};

export type DiagnosticoDetalheApi = {
  id: string;
  empresa_razao_social: string;
  empresa_cnpj?: string;
  criado_em?: string | null;
  finalizado_em?: string | null;
  plano: string;
  status: string;
  relatorio_pdf_url: string | null;
  checklist: FrenteChecklist[] | null;
  matriz_impacto: MatrizLinha[] | null;
  cronograma: CronogramaFase[] | null;
  /** Likert 1–5 por controle M12 (API); booleanos legados são normalizados na leitura. */
  checklist_m12_autoconf: (number | boolean)[] | null;
  /** Chave canónica f{i}_a{j} — meta de prazo (ISO) e vários comentários por ação sugerida. */
  quadro_implantacao_anotacoes?: Record<string, QuadroItemPersistidoApi> | null;
  versao_otimista: number | null;
  versao_plano?: number;
  score: {
    score_geral: { valor: number };
    score_por_dimensao: Record<string, { valor: number; peso_total_aplicado: number }>;
  } | null;
};

const M12_NUM_ITENS = 10;

function normalizarM12DoApi(
  raw: DiagnosticoDetalheApi["checklist_m12_autoconf"],
): number[] | null {
  if (!Array.isArray(raw) || raw.length !== M12_NUM_ITENS) return null;
  const out: number[] = [];
  for (const x of raw) {
    if (typeof x === "boolean") out.push(x ? 5 : 1);
    else if (typeof x === "number" && Number.isInteger(x) && x >= 1 && x <= 5) out.push(x);
    else return null;
  }
  return out;
}

/** Estado local antes de qualquer escolha do utilizador — sem Likert por defeito. */
function m12EstadoInicialVazio(): (number | null)[] {
  return Array.from({ length: M12_NUM_ITENS }, () => null);
}

/** Só persiste na API quando os 10 controles têm inteiro 1–5. */
function m12ValoresSeCompleto(vals: (number | null)[]): number[] | null {
  if (!Array.isArray(vals) || vals.length !== M12_NUM_ITENS) return null;
  const out: number[] = [];
  for (const x of vals) {
    if (x === null || typeof x !== "number" || !Number.isInteger(x) || x < 1 || x > 5) {
      return null;
    }
    out.push(x);
  }
  return out;
}

function rotuloLikertM12(v: number): string {
  const m: Record<number, string> = {
    1: "Não implementado",
    2: "Inicial / informal",
    3: "Parcial",
    4: "Implementado (lacunas menores)",
    5: "Implementado e monitorado",
  };
  return m[v] ?? "—";
}

/** Estado local do quadro por ação (edição + espelho do persistido até PATCH). */
export type QuadroEdicaoAcao = {
  prazo_meta: string;
  comentarios: string[];
  /** Vazio = exibir descrição sugerida pelo motor; preenchido = sobrescreve após salvar. */
  descricao_personalizada: string;
};

function defaultQuadroEdicaoAcao(): QuadroEdicaoAcao {
  return {
    prazo_meta: "",
    comentarios: [],
    descricao_personalizada: "",
  };
}

/** Exibe meta ISO (YYYY-MM-DD) em pt-BR curto. */
function formatarMetaPrazoPtBr(iso: string): string {
  const s = (iso || "").trim();
  if (s.length !== 10 || s[4] !== "-" || s[7] !== "-") return s || "—";
  const [y, m, d] = s.split("-");
  return `${d}/${m}/${y}`;
}

function chaveQuadroParaAcao(acao: AcaoChecklist, i: number, j: number): string {
  const pid = (acao.plano_acao_id || "").trim();
  if (pid.length >= 32 && /^[0-9a-f-]+$/i.test(pid)) {
    return pid;
  }
  return `f${i}_a${j}`;
}

function chavesQuadroIniciais(
  checklist: FrenteChecklist[] | null | undefined,
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
      const prazo_meta = typeof p?.prazo_meta === "string" ? p.prazo_meta : "";
      const descricao_personalizada =
        typeof p?.descricao_personalizada === "string" ? p.descricao_personalizada.trim() : "";
      out[k] = {
        prazo_meta,
        comentarios,
        descricao_personalizada,
      };
    });
  });
  return out;
}

function mockDiagnostico(id: string): DiagnosticoDetalheApi {
  const isAvancado = id.startsWith("7");
  return {
    id,
    empresa_razao_social: isAvancado ? "Acme Corp S/A" : "Tech Solutions Ltda",
    plano: isAvancado ? "avancado" : "gratuito",
    status: "finalizado",
    relatorio_pdf_url: null,
    cronograma: [
      {
        fase: "Curto prazo (0-12 meses)",
        foco: "Governança e mapeamento.",
        referencia_normativa: "LC 214/2025",
      },
    ],
    matriz_impacto: [
      {
        departamento: "Fiscal",
        impacto_resumo: "Exemplo: apuração CBS.",
        criticidade: "Crítica",
        base_legal: "LC 214/2025",
      },
    ],
    checklist_m12_autoconf: null,
    quadro_implantacao_anotacoes: null,
    versao_otimista: 1,
    score: {
      score_geral: { valor: 62 },
      score_por_dimensao: {
        fiscal: { valor: 55, peso_total_aplicado: 1.5 },
        tecnologica: { valor: 48, peso_total_aplicado: 1.4 },
        compliance_abnt_17301: { valor: 70, peso_total_aplicado: 1.5 },
      },
    },
    checklist: [
      {
        nome: "Governança e Comitê",
        acoes: [
          {
            descricao: "Constituir Comitê Tributário Reforma",
            responsavel: "Diretoria",
            prazo: "Out/2025",
            criticidade: "Crítica",
            prioridade: 10,
            base_legal: "LC 214/2025 art. 5º",
          },
        ],
      },
    ],
  };
}

function corHeat(valor: number): string {
  if (valor < 40) return "bg-red-500/85";
  if (valor < 60) return "bg-amber-500/80";
  if (valor < 75) return "bg-yellow-400/80";
  return "bg-emerald-500/75";
}

export default function DiagnosticoDetalheClient({ id }: { id: string }) {
  const router = useRouter();
  const [data, setData] = useState<DiagnosticoDetalheApi | null>(null);
  const [error, setError] = useState<string | null>(null);
  const versaoOtimistaRef = useRef<number | null>(null);
  const [quadroEdits, setQuadroEdits] = useState<Record<string, QuadroEdicaoAcao>>({});
  /** Gravação por chave f{i}_a{j} (uma ação de cada vez). */
  const [quadroSaving, setQuadroSaving] = useState<Record<string, boolean>>({});
  const [quadroMsgPorAcao, setQuadroMsgPorAcao] = useState<Record<string, string>>({});
  const [prazoModalQk, setPrazoModalQk] = useState<string | null>(null);
  const [prazoModalDraft, setPrazoModalDraft] = useState("");
  const [comentarioModalQk, setComentarioModalQk] = useState<string | null>(null);
  const [comentarioModalDraft, setComentarioModalDraft] = useState("");
  const [acaoEditModalQk, setAcaoEditModalQk] = useState<string | null>(null);
  const [acaoEditModalDraft, setAcaoEditModalDraft] = useState("");
  const [m12Likert, setM12Likert] = useState<(number | null)[]>([]);
  const [m12ModalIndex, setM12ModalIndex] = useState<number | null>(null);
  const [m12ModalDraft, setM12ModalDraft] = useState<number | null>(null);
  const [m12Saving, setM12Saving] = useState(false);
  const [m12Msg, setM12Msg] = useState<string | null>(null);

  useEffect(() => {
    let cancel = false;
    (async () => {
      const token = getAccessToken();
      const base = getApiUrlForFetch().replace(/\/$/, "");
      try {
        const res = await fetch(`${base}/diagnosticos/${id}`, {
          headers: {
            Accept: "application/json",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
          cache: "no-store",
        });
        if (!res.ok) {
          if (encerrarSessaoPainelSe401(res.status)) return;
          if (!cancel) {
            setError(`API ${res.status}`);
            setData(mockDiagnostico(id));
          }
          return;
        }
        const json = (await res.json()) as DiagnosticoDetalheApi;
        if (!cancel) {
          if (json.versao_otimista != null) {
            versaoOtimistaRef.current = json.versao_otimista;
          }
          setData(json);
          setError(null);
        }
      } catch {
        if (!cancel) {
          setError("Falha de rede — exibindo dados de exemplo.");
          setData(mockDiagnostico(id));
        }
      }
    })();
    return () => {
      cancel = true;
    };
  }, [id]);

  const radarData = useMemo(() => {
    if (!data?.score?.score_por_dimensao) return null;
    return Object.entries(data.score.score_por_dimensao).map(([dim, s]) => ({
      dimensao: dim.replace(/_/g, " "),
      valor: s.valor,
    }));
  }, [data]);

  const rankingGaps = useMemo(() => {
    if (!data?.score?.score_por_dimensao) return [];
    return Object.entries(data.score.score_por_dimensao)
      .map(([dim, s]) => ({
        dimensao: dim.replace(/_/g, " "),
        valor: s.valor,
      }))
      .sort((a, b) => a.valor - b.valor);
  }, [data]);

  /** M12 — frente checklist ABNT 10 itens (mesmo texto retornado pela API). */
  const frenteAbnt10 = useMemo(() => {
    return (
      data?.checklist?.find((f) => f.nome.includes("17301") && f.nome.includes("10")) ?? null
    );
  }, [data?.checklist]);

  useEffect(() => {
    if (!frenteAbnt10 || frenteAbnt10.acoes.length !== M12_NUM_ITENS) return;
    const parsed = normalizarM12DoApi(data?.checklist_m12_autoconf ?? null);
    setM12Likert(parsed ? [...parsed] : m12EstadoInicialVazio());
    setM12Msg(null);
  }, [data?.checklist_m12_autoconf, data?.id, frenteAbnt10]);

  useEffect(() => {
    if (data?.versao_otimista != null) {
      versaoOtimistaRef.current = data.versao_otimista;
    }
  }, [data?.versao_otimista]);

  useEffect(() => {
    if (!data?.checklist) return;
    setQuadroEdits(chavesQuadroIniciais(data.checklist, data.quadro_implantacao_anotacoes));
  }, [data?.id, data?.checklist, data?.quadro_implantacao_anotacoes]);

  useEffect(() => {
    setQuadroMsgPorAcao({});
  }, [data?.id]);

  const refetchDetalhe = useCallback(async () => {
    const token = getAccessToken();
    const base = getApiUrlForFetch().replace(/\/$/, "");
    const res = await fetch(`${base}/diagnosticos/${id}`, {
      headers: {
        Accept: "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      cache: "no-store",
    });
    if (!res.ok) {
      if (encerrarSessaoPainelSe401(res.status)) return;
      return;
    }
    const json = (await res.json()) as DiagnosticoDetalheApi;
    if (json.versao_otimista != null) {
      versaoOtimistaRef.current = json.versao_otimista;
    }
    setData(json);
  }, [id]);

  const salvarQuadroAcao = useCallback(
    async (qk: string, snapshot?: Partial<QuadroEdicaoAcao>): Promise<boolean> => {
      const token = getAccessToken();
      if (!token || data?.status !== "finalizado") {
        setQuadroMsgPorAcao((prev) => ({
          ...prev,
          [qk]: "É necessário estar autenticado e o diagnóstico finalizado.",
        }));
        return false;
      }
      const v = versaoOtimistaRef.current;
      if (v == null) {
        setQuadroMsgPorAcao((prev) => ({
          ...prev,
          [qk]: "Versão otimista indisponível — recarregue a página.",
        }));
        return false;
      }
      const qv: QuadroEdicaoAcao = {
        ...defaultQuadroEdicaoAcao(),
        ...quadroEdits[qk],
        ...snapshot,
      };
      const limpos = qv.comentarios.map((s) => s.trim()).filter(Boolean);
      const body: Record<
        string,
        { prazo_meta: string; comentarios: string[]; descricao_personalizada: string }
      > = {
        [qk]: {
          prazo_meta: qv.prazo_meta.trim(),
          comentarios: limpos,
          descricao_personalizada: (qv.descricao_personalizada ?? "").trim(),
        },
      };

      setQuadroSaving((s) => ({ ...s, [qk]: true }));
      setQuadroMsgPorAcao((prev) => {
        const next = { ...prev };
        delete next[qk];
        return next;
      });
      const base = getApiUrlForFetch().replace(/\/$/, "");
      try {
        const res = await fetch(`${base}/diagnosticos/${id}/quadro-implantacao-anotacoes`, {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
            Accept: "application/json",
            Authorization: `Bearer ${token}`,
            "If-Match": String(v),
          },
          body: JSON.stringify({ quadro_implantacao_anotacoes: body }),
        });
        if (encerrarSessaoPainelSe401(res.status)) return false;
        if (res.ok) {
          const json = (await res.json()) as DiagnosticoDetalheApi;
          if (json.versao_otimista != null) {
            versaoOtimistaRef.current = json.versao_otimista;
          }
          setData(json);
          setQuadroMsgPorAcao((prev) => ({ ...prev, [qk]: "Ação gravada." }));
          return true;
        }
        if (res.status === 412) {
          setQuadroMsgPorAcao((prev) => ({
            ...prev,
            [qk]: "Conflito de versão — recarregando…",
          }));
          await refetchDetalhe();
          return false;
        }
        const t = await res.text();
        setQuadroMsgPorAcao((prev) => ({
          ...prev,
          [qk]: `Não foi possível gravar (${res.status}): ${t.slice(0, 200)}`,
        }));
        return false;
      } catch {
        setQuadroMsgPorAcao((prev) => ({
          ...prev,
          [qk]: "Falha de rede ao gravar.",
        }));
        return false;
      } finally {
        setQuadroSaving((s) => ({ ...s, [qk]: false }));
      }
    },
    [data?.status, id, quadroEdits, refetchDetalhe],
  );

  const abrirModalPrazoParaChave = useCallback(
    (qk: string) => {
      const atual = { ...defaultQuadroEdicaoAcao(), ...quadroEdits[qk] };
      setPrazoModalDraft(atual.prazo_meta);
      setPrazoModalQk(qk);
    },
    [quadroEdits],
  );

  const confirmarPrazoModal = useCallback(async () => {
    const qk = prazoModalQk;
    if (!qk) return;
    const iso = prazoModalDraft.trim();
    if (iso !== "" && (iso.length !== 10 || iso[4] !== "-" || iso[7] !== "-")) {
      setQuadroMsgPorAcao((prev) => ({
        ...prev,
        [qk]: "Use a data no calendário (formato YYYY-MM-DD) ou deixe em branco para limpar.",
      }));
      return;
    }
    await salvarQuadroAcao(qk, { prazo_meta: iso });
    setPrazoModalQk(null);
  }, [prazoModalQk, prazoModalDraft, salvarQuadroAcao]);

  const removerPrazoDaChave = useCallback(
    async (qk: string) => {
      await salvarQuadroAcao(qk, { prazo_meta: "" });
    },
    [salvarQuadroAcao],
  );

  const abrirModalComentarioParaChave = useCallback((qk: string) => {
    setComentarioModalDraft("");
    setComentarioModalQk(qk);
  }, []);

  const confirmarComentarioModal = useCallback(async () => {
    const qk = comentarioModalQk;
    if (!qk) return;
    const t = comentarioModalDraft.trim();
    if (!t) {
      setComentarioModalQk(null);
      return;
    }
    const cur = { ...defaultQuadroEdicaoAcao(), ...quadroEdits[qk] };
    await salvarQuadroAcao(qk, { comentarios: [...cur.comentarios, t] });
    setComentarioModalDraft("");
    setComentarioModalQk(null);
  }, [comentarioModalQk, comentarioModalDraft, quadroEdits, salvarQuadroAcao]);

  const removerComentarioDaChave = useCallback(
    async (qk: string, idx: number) => {
      const cur = { ...defaultQuadroEdicaoAcao(), ...quadroEdits[qk] };
      const next = cur.comentarios.filter((_, i) => i !== idx);
      void salvarQuadroAcao(qk, { comentarios: next });
    },
    [quadroEdits, salvarQuadroAcao],
  );

  const abrirModalAcaoEditParaChave = useCallback(
    (qk: string) => {
      const atual = { ...defaultQuadroEdicaoAcao(), ...quadroEdits[qk] };
      setAcaoEditModalDraft(atual.descricao_personalizada ?? "");
      setAcaoEditModalQk(qk);
    },
    [quadroEdits],
  );

  const confirmarAcaoEditModal = useCallback(async () => {
    const qk = acaoEditModalQk;
    if (!qk) return;
    const ok = await salvarQuadroAcao(qk, {
      descricao_personalizada: acaoEditModalDraft.trim(),
    });
    if (ok) setAcaoEditModalQk(null);
  }, [acaoEditModalQk, acaoEditModalDraft, salvarQuadroAcao]);

  const salvarM12LikertCompleto = useCallback(
    async (proximo: number[]): Promise<boolean> => {
      const token = getAccessToken();
      if (!token || data?.status !== "finalizado") {
        setM12Msg("É necessário estar autenticado e o diagnóstico finalizado.");
        return false;
      }
      const v = versaoOtimistaRef.current;
      if (v == null) {
        setM12Msg("Versão otimista indisponível — recarregue a página.");
        return false;
      }
      setM12Saving(true);
      setM12Msg(null);
      const base = getApiUrlForFetch().replace(/\/$/, "");
      try {
        const res = await fetch(`${base}/diagnosticos/${id}/checklist-m12-autoconf`, {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
            Accept: "application/json",
            Authorization: `Bearer ${token}`,
            "If-Match": String(v),
          },
          body: JSON.stringify({ checklist_m12_autoconf: proximo }),
        });
        if (encerrarSessaoPainelSe401(res.status)) return false;
        if (res.ok) {
          const json = (await res.json()) as DiagnosticoDetalheApi;
          if (json.versao_otimista != null) {
            versaoOtimistaRef.current = json.versao_otimista;
          }
          const sync = normalizarM12DoApi(json.checklist_m12_autoconf);
          setM12Likert(sync ? [...sync] : [...proximo]);
          setData(json);
          setM12Msg("Autoconf M12 gravada.");
          return true;
        }
        if (res.status === 412) {
          setM12Msg("Conflito de versão — a atualizar dados…");
          await refetchDetalhe();
          return false;
        }
        const t = await res.text();
        setM12Msg(`Não foi possível gravar (${res.status}): ${t.slice(0, 160)}`);
        return false;
      } catch {
        setM12Msg("Falha de rede ao gravar o M12.");
        return false;
      } finally {
        setM12Saving(false);
      }
    },
    [data?.status, id, refetchDetalhe],
  );

  const gravarM12NaApi = useCallback(async () => {
    const payload = m12ValoresSeCompleto(m12Likert);
    if (!payload) {
      setM12Msg("Assine os 10 controles (nível 1 a 5 em cada um) antes de gravar na API.");
      return;
    }
    await salvarM12LikertCompleto(payload);
  }, [m12Likert, salvarM12LikertCompleto]);

  const confirmarM12Modal = useCallback(() => {
    const idx = m12ModalIndex;
    if (idx === null || idx < 0 || idx >= M12_NUM_ITENS || m12ModalDraft === null) return;
    setM12Likert((prev) => {
      const base =
        prev.length === M12_NUM_ITENS ? [...prev] : m12EstadoInicialVazio();
      base[idx] = m12ModalDraft;
      return base;
    });
    setM12ModalIndex(null);
  }, [m12ModalIndex, m12ModalDraft]);

  const m12ProgressoAssinalados = m12Likert.filter((x) => x !== null).length;
  const m12CompletoParaApi = m12ValoresSeCompleto(m12Likert) !== null;

  const barGapColors = ["#b91c1c", "#ea580c", "#ca8a04", "#65a30d", "#16a34a"];

  /** Plano avançado: novo fluxo no assistente sem herdar rascunho local nem pendência de gravação. */
  const irRefazerDiagnostico = useCallback(() => {
    clearWizardDraft();
    clearPendingDiagnosticoFromStorage();
    router.push("/wizard");
  }, [router]);

  if (!data) {
    return (
      <div className="container py-10 text-muted-foreground">
        Carregando diagnóstico…
      </div>
    );
  }

  return (
    <div className="container py-10">
      <div className="mb-8">
        <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-sm mb-4">
          <Link href="/dashboard/diagnosticos" className="text-primary hover:underline">
            ← Voltar para Dashboard
          </Link>
          <span className="text-muted-foreground">·</span>
          <Link href="/abnt-framework" className="text-primary hover:underline">
            Guia ABNT / PDCA (M11)
          </Link>
        </div>
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <h1 className="text-3xl font-bold">{data.empresa_razao_social}</h1>
            <p className="text-muted-foreground">ID do Diagnóstico: {data.id}</p>
            {error && (
              <p className="text-sm text-amber-600 mt-2">
                {error} — dados podem ser mock locais.
              </p>
            )}
          </div>
          <div className="flex flex-wrap gap-2 items-center">
            <Badge variant={data.plano === "gratuito" ? "secondary" : "default"} className="text-sm px-4 py-1">
              PLANO {data.plano.toUpperCase()}
            </Badge>
            {data.empresa_cnpj && data.empresa_cnpj.replace(/\D/g, "").length === 14 ? (
              <>
                <Button variant="secondary" size="sm" asChild className="gap-2">
                  <Link
                    href={buildEmpresaDiagnosticosHref(data.empresa_cnpj, data.empresa_razao_social)}
                  >
                    Grelha da empresa
                  </Link>
                </Button>
                <Button variant="outline" size="sm" asChild className="gap-2">
                  <Link href={buildWizardUrlNovaDiagnosticoEmpresa(data.empresa_cnpj, data.empresa_razao_social)}>
                    Novo diagnóstico (mesma empresa)
                  </Link>
                </Button>
              </>
            ) : null}
            {data.plano === "avancado" ? (
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={irRefazerDiagnostico}
                className="gap-2"
              >
                <RefreshCw className="h-4 w-4 shrink-0" aria-hidden />
                Refazer diagnóstico
              </Button>
            ) : null}
            {data.relatorio_pdf_url && (
              <Button variant="default" size="sm" asChild>
                <a
                  href={normalizarHrefRelatorioPdf(data.relatorio_pdf_url) ?? data.relatorio_pdf_url}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Abrir relatório PDF
                </a>
              </Button>
            )}
          </div>
        </div>
      </div>

      <PrivacidadeDiagnosticoCard diagnosticoId={data.id} diagnosticoStatus={data.status} />

      <RetificacaoDiagnosticoCard diagnosticoId={data.id} diagnosticoStatus={data.status} />

      {radarData && radarData.length > 0 && (
        <Card className="mb-10">
          <CardHeader>
            <CardTitle>Radar por dimensão</CardTitle>
          </CardHeader>
          <CardContent className="h-[340px]">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart data={radarData} cx="50%" cy="50%" outerRadius="80%">
                <PolarGrid />
                <PolarAngleAxis dataKey="dimensao" tick={{ fontSize: 11 }} />
                <Radar name="Score" dataKey="valor" stroke="#2563eb" fill="#3b82f6" fillOpacity={0.35} />
              </RadarChart>
            </ResponsiveContainer>
            {data.score?.score_geral && (
              <p className="text-center text-sm text-muted-foreground mt-2">
                Score geral: <strong>{data.score.score_geral.valor}</strong> / 100
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {rankingGaps.length > 0 && (
        <div className="space-y-8 mb-10">
          <section
            aria-labelledby="m05-ranking-gaps-heading"
            className="rounded-xl border bg-card px-4 py-5 sm:px-6 sm:py-6 shadow-sm"
          >
            <h2 id="m05-ranking-gaps-heading" className="text-lg font-semibold tracking-tight mb-4">
              Ranking explícito de gaps (M05)
            </h2>
            <p className="text-sm text-muted-foreground mb-4">
              Ordem: menor score por dimensão primeiro — espelha o mesmo conjunto usado no heatmap e no gráfico de barras.
            </p>
            <ol className="list-decimal list-inside space-y-2 text-sm sm:text-base">
              {rankingGaps.map((row, idx) => (
                <li key={row.dimensao} className="marker:font-semibold">
                  <span className="capitalize font-medium text-foreground">{row.dimensao}</span>
                  <span className="text-muted-foreground"> — score </span>
                  <span className="tabular-nums font-semibold text-foreground">
                    {row.valor.toFixed(1)}
                  </span>
                  <span className="text-muted-foreground"> / 100</span>
                  {idx === 0 ? (
                    <span className="sr-only"> (prioridade máxima — maior gap)</span>
                  ) : null}
                </li>
              ))}
            </ol>
          </section>

          <div className="grid md:grid-cols-2 gap-8">
          <Card>
            <CardHeader>
              <CardTitle>Heatmap rápido por dimensão (M05)</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground mb-4">
                Intensidade da cor: menor score (vermelho) = maior gap relativo no diagnóstico.
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {rankingGaps.map((row) => (
                  <div
                    key={row.dimensao}
                    className={`rounded-md px-3 py-2 text-sm text-white flex justify-between ${corHeat(row.valor)}`}
                  >
                    <span className="font-medium capitalize">{row.dimensao}</span>
                    <span>{row.valor.toFixed(0)}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Ranking de gaps (menores scores)</CardTitle>
            </CardHeader>
            <CardContent className="h-[280px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={rankingGaps}
                  layout="vertical"
                  margin={{ left: 8, right: 16 }}
                >
                  <XAxis type="number" domain={[0, 100]} />
                  <YAxis type="category" dataKey="dimensao" width={120} tick={{ fontSize: 11 }} />
                  <Tooltip
                    formatter={(v) => [
                      `${typeof v === "number" ? v.toFixed(1) : String(v ?? "")} / 100`,
                      "Score",
                    ]}
                  />
                  <Bar dataKey="valor" radius={[0, 4, 4, 0]}>
                    {rankingGaps.map((_, i) => (
                      <Cell key={i} fill={barGapColors[Math.min(i, barGapColors.length - 1)]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
          </div>
        </div>
      )}

      {data.cronograma && data.cronograma.length > 0 && (
        <Card className="mb-10">
          <CardHeader>
            <CardTitle id="m06-cronograma-tabela-heading">
              Cronograma em cinco horizontes (LC 214/2025)
            </CardTitle>
          </CardHeader>
          <CardContent className="overflow-x-auto">
            <table
              className="w-full text-sm border-collapse"
              aria-labelledby="m06-cronograma-tabela-heading"
            >
              <thead>
                <tr className="border-b">
                  <th scope="col" className="text-left py-2 pr-4">
                    Fase
                  </th>
                  <th scope="col" className="text-left py-2 pr-4">
                    Foco
                  </th>
                  <th scope="col" className="text-left py-2">
                    Referência normativa
                  </th>
                </tr>
              </thead>
              <tbody>
                {data.cronograma.map((linha) => (
                  <tr key={linha.fase} className="border-b border-muted">
                    <td className="py-2 pr-4 font-medium align-top">{linha.fase}</td>
                    <td className="py-2 pr-4 align-top">{linha.foco}</td>
                    <td className="py-2 text-muted-foreground align-top italic">{linha.referencia_normativa}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div
              className="mt-8 rounded-xl border border-border/80 bg-muted/25 p-5 sm:p-7 motion-reduce:transition-none"
              role="region"
              aria-label="Linha do tempo do cronograma em cinco fases (M06)"
            >
              <p
                id="m06-timeline-heading"
                className="text-sm font-semibold mb-6 tracking-tight text-foreground"
              >
                Linha do tempo (M06 — visão rápida)
              </p>
              <ol
                className="relative ml-2 border-l-[3px] border-primary/70 space-y-12 pl-8 sm:pl-11 motion-reduce:space-y-8"
                aria-labelledby="m06-timeline-heading"
              >
                {(data.cronograma ?? []).map((linha, idx) => (
                  <li
                    key={linha.fase}
                    className="relative scroll-mt-4 rounded-md outline-none focus-within:ring-2 focus-within:ring-primary/50 focus-within:ring-offset-2 focus-within:ring-offset-background"
                  >
                    <span
                      className="absolute -left-[26px] sm:-left-[30px] top-1 flex h-4 w-4 rounded-full bg-primary shadow-md ring-[3px] ring-background motion-reduce:shadow-none"
                      aria-hidden
                    />
                    <span className="sr-only">
                      Fase {idx + 1} de {(data.cronograma ?? []).length}
                    </span>
                    <p className="font-semibold text-sm leading-snug text-foreground">{linha.fase}</p>
                    <p className="text-sm text-muted-foreground mt-1.5 leading-relaxed">{linha.foco}</p>
                    <p className="text-xs text-muted-foreground mt-2 italic border-l-2 border-muted pl-3">
                      {linha.referencia_normativa}
                    </p>
                  </li>
                ))}
              </ol>
            </div>
          </CardContent>
        </Card>
      )}

      {frenteAbnt10 && frenteAbnt10.acoes.length > 0 && (
        <Card className="mb-10">
          <CardHeader>
            <CardTitle>Autoconferência ABNT — 10 controles (M12)</CardTitle>
            <p className="text-sm font-normal text-muted-foreground">
              Escala Likert 1 (mínimo) a 5 (máximo) por controle — espelho do checklist do relatório PDF.{" "}
              <strong className="font-medium text-foreground">Alterar</strong> aplica o nível apenas neste controle
              (sem valores por defeito). Depois de <strong className="font-medium text-foreground">10/10 assinalados</strong>, use{" "}
              <strong className="font-medium text-foreground">Gravar autoconf na API</strong> (
              <code className="text-xs">If-Match</code> / <code className="text-xs">versao_otimista</code>) — ABNT NBR
              17301:2026; LC 214/2025.
            </p>
            {data.status === "finalizado" ? (
              <p
                className="text-sm leading-snug border rounded-md p-3 mt-3 bg-muted/25 text-muted-foreground"
                role="note"
              >
                <strong className="text-foreground">Independente do assistente:</strong> estas notas não são copiadas
                do questionário («Inexistente», «Incipiente», etc.). Cada controle tem de ser escolhido aqui.
              </p>
            ) : null}
            {data.status === "finalizado" ? (
              <div className="flex flex-col gap-3 mt-4 sm:flex-row sm:flex-wrap sm:items-center sm:justify-between">
                <p className="text-sm font-medium text-foreground tabular-nums">
                  Progresso: {m12ProgressoAssinalados}/{M12_NUM_ITENS} controles assinalados
                </p>
                <Button
                  type="button"
                  disabled={m12Saving || data.status !== "finalizado" || !m12CompletoParaApi}
                  onClick={() => void gravarM12NaApi()}
                >
                  {m12Saving ? "Gravando…" : "Gravar autoconf na API"}
                </Button>
              </div>
            ) : null}
            {m12Msg ? (
              <p className="text-sm text-muted-foreground mt-2" role="status">
                {m12Msg}
              </p>
            ) : null}
          </CardHeader>
          <CardContent className="space-y-3">
            {frenteAbnt10.acoes.map((a, i) => {
              const valor = m12Likert[i] ?? null;
              return (
                <div
                  key={a.descricao + String(i)}
                  className="flex flex-col gap-3 rounded-lg border bg-muted/10 p-3 sm:flex-row sm:items-start sm:justify-between sm:gap-4"
                >
                  <p className="text-sm leading-snug flex-1 min-w-0">{a.descricao}</p>
                  <div className="flex flex-wrap items-center gap-2 shrink-0">
                    <Badge variant="secondary" className="text-xs font-normal max-w-[14rem] sm:max-w-xs text-left">
                      {valor === null || valor === undefined
                        ? "Não assinalado — use Alterar"
                        : `${valor} — ${rotuloLikertM12(valor)}`}
                    </Badge>
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      className="gap-1.5"
                      disabled={m12Saving || data.status !== "finalizado"}
                      onClick={() => {
                        setM12ModalIndex(i);
                        setM12ModalDraft(valor ?? null);
                      }}
                    >
                      <Pencil className="h-3.5 w-3.5 shrink-0" aria-hidden />
                      Alterar
                    </Button>
                  </div>
                </div>
              );
            })}
          </CardContent>
        </Card>
      )}

      {data.matriz_impacto && data.matriz_impacto.length > 0 && (
        <Card className="mb-10">
          <CardHeader>
            <CardTitle>Matriz de impacto por departamento</CardTitle>
          </CardHeader>
          <CardContent className="overflow-x-auto">
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2 pr-4">Departamento</th>
                  <th className="text-left py-2 pr-4">Impacto</th>
                  <th className="text-left py-2 pr-4">Criticidade</th>
                  <th className="text-left py-2">Base legal</th>
                </tr>
              </thead>
              <tbody>
                {data.matriz_impacto.map((m) => (
                  <tr key={m.departamento} className="border-b border-muted">
                    <td className="py-2 pr-4 font-medium">{m.departamento}</td>
                    <td className="py-2 pr-4">{m.impacto_resumo}</td>
                    <td className="py-2 pr-4">
                      <Badge variant={m.criticidade === "Crítica" ? "destructive" : "secondary"}>
                        {m.criticidade}
                      </Badge>
                    </td>
                    <td className="py-2 text-muted-foreground text-xs">{m.base_legal ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>
      )}

      <div className="space-y-8">
        <div className="flex flex-col gap-3 sm:flex-row sm:justify-between sm:items-start flex-wrap gap-4">
          <div>
            <h2 className="text-2xl font-bold tracking-tight">Quadro de implantação</h2>
            <p className="text-sm text-muted-foreground mt-1 max-w-2xl">
              <strong className="font-medium text-foreground">Alterar ação</strong> abre a edição do texto do cartão
              com <strong className="font-medium text-foreground">Salvar</strong> na janela.{" "}
              <strong className="font-medium text-foreground">Incluir prazo</strong> e{" "}
              <strong className="font-medium text-foreground">Adicionar comentário</strong> também gravam na confirmação
              (If-Match / <code className="text-xs">versao_otimista</code>). Referência do motor: prazo qualitativo na
              ficha.
            </p>
          </div>
          <div className="flex flex-wrap gap-2 items-center shrink-0">
            <Button variant="outline" type="button" disabled>
              Exportar CSV (em breve)
            </Button>
          </div>
        </div>

        <div className="flex gap-6 overflow-x-auto pb-4">
          <div className="flex-1 min-w-[320px] bg-slate-100 rounded-lg p-4">
            <h3 className="font-semibold text-slate-700 mb-4 flex items-center justify-between">
              Ações sugeridas
              <Badge variant="secondary">
                {data.checklist?.reduce((acc, f) => acc + f.acoes.length, 0) ?? 0}
              </Badge>
            </h3>
            <div className="space-y-3">
              {data.checklist?.map((frente, i) => (
                <div key={i}>
                  <div className="text-xs font-bold text-slate-500 uppercase mb-2 mt-4 first:mt-0">
                    {frente.nome}
                  </div>
                  {frente.acoes.map((acao, j) => {
                    const qk = chaveQuadroParaAcao(acao, i, j);
                    const qv = quadroEdits[qk] ?? defaultQuadroEdicaoAcao();
                    const descMotor = acao.descricao;
                    const descEditada = (qv.descricao_personalizada ?? "").trim();
                    const tituloExibido = descEditada || descMotor;
                    return (
                    <Card
                      key={qk}
                      className="mb-2 hover:border-primary/50 transition-colors"
                    >
                      <CardHeader className="p-4 pb-2">
                        <div className="flex items-start justify-between gap-2">
                          <CardTitle className="text-sm font-medium leading-tight">
                            {tituloExibido}
                          </CardTitle>
                          {acao.prioridade != null && (
                            <Badge variant="outline" className="shrink-0 text-[10px]">
                              #{acao.prioridade}
                            </Badge>
                          )}
                        </div>
                        {descEditada ? (
                          <p className="text-xs text-muted-foreground mt-1.5 leading-snug">
                            Texto sugerido pelo motor: {descMotor}
                          </p>
                        ) : null}
                        {acao.base_legal && (
                          <p className="text-xs text-muted-foreground mt-1">
                            Base legal: {acao.base_legal}
                          </p>
                        )}
                      </CardHeader>
                      <CardContent className="p-4 pt-0 space-y-3">
                        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            className="w-full sm:w-auto gap-2"
                            disabled={Boolean(quadroSaving[qk]) || data.status !== "finalizado"}
                            onClick={() => abrirModalAcaoEditParaChave(qk)}
                          >
                            <Pencil className="h-3.5 w-3.5 shrink-0" aria-hidden />
                            Alterar ação
                          </Button>
                          {quadroMsgPorAcao[qk] ? (
                            <p className="text-xs text-muted-foreground sm:text-right" role="status">
                              {quadroMsgPorAcao[qk]}
                            </p>
                          ) : null}
                        </div>
                        <div className="flex justify-between items-center mt-2">
                          <span className="text-xs text-muted-foreground">{acao.responsavel}</span>
                          <Badge
                            variant={acao.criticidade === "Crítica" ? "destructive" : "secondary"}
                            className="text-[10px]"
                          >
                            {acao.criticidade}
                          </Badge>
                        </div>
                        <p className="text-xs text-muted-foreground">
                          Referência motor (prazo qualitativo): {acao.prazo}
                        </p>
                        <div className="space-y-2 rounded-md border border-border/60 bg-muted/20 px-3 py-2.5">
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <span className="text-xs font-medium text-foreground">Prazo planejado (meta)</span>
                            <div className="flex flex-wrap gap-1.5">
                              <Button
                                type="button"
                                variant="outline"
                                size="sm"
                                className="h-8 gap-1.5 text-xs"
                                disabled={Boolean(quadroSaving[qk]) || data.status !== "finalizado"}
                                onClick={() => abrirModalPrazoParaChave(qk)}
                              >
                                <CalendarPlus className="h-3.5 w-3.5 shrink-0" aria-hidden />
                                {qv.prazo_meta.trim() ? "Alterar prazo" : "Incluir prazo"}
                              </Button>
                              {qv.prazo_meta.trim() ? (
                                <Button
                                  type="button"
                                  variant="ghost"
                                  size="sm"
                                  className="h-8 text-xs text-muted-foreground"
                                  disabled={Boolean(quadroSaving[qk]) || data.status !== "finalizado"}
                                  onClick={() => void removerPrazoDaChave(qk)}
                                >
                                  Remover prazo
                                </Button>
                              ) : null}
                            </div>
                          </div>
                          <p className="text-xs text-muted-foreground">
                            {qv.prazo_meta.trim() ? (
                              <>
                                Meta gravada:{" "}
                                <span className="font-medium text-foreground tabular-nums">
                                  {formatarMetaPrazoPtBr(qv.prazo_meta)}
                                </span>{" "}
                                <span className="text-muted-foreground/80">({qv.prazo_meta})</span>
                              </>
                            ) : (
                              <>Nenhuma meta de prazo — use «Incluir prazo» para definir em uma janela.</>
                            )}
                          </p>
                        </div>
                        <div className="space-y-2">
                          <div className="flex items-center justify-between gap-2">
                            <Label className="text-xs">Comentários</Label>
                            <Button
                              type="button"
                              variant="outline"
                              size="sm"
                              className="h-7 gap-1 text-xs"
                              disabled={Boolean(quadroSaving[qk]) || data.status !== "finalizado"}
                              onClick={() => abrirModalComentarioParaChave(qk)}
                            >
                              <Plus className="h-3.5 w-3.5 shrink-0" aria-hidden />
                              Adicionar comentário
                            </Button>
                          </div>
                          {qv.comentarios.length === 0 ? (
                            <p className="text-xs text-muted-foreground">
                              Nenhum comentário — use «Adicionar comentário» para abrir a janela e gravar na confirmação.
                            </p>
                          ) : (
                            <ul className="space-y-2 list-none p-0 m-0">
                              {qv.comentarios.map((texto, idx) => (
                                <li
                                  key={`${qk}-c-${idx}`}
                                  className="flex gap-2 items-start rounded-md border border-border/50 bg-background/80 px-2.5 py-2"
                                >
                                  <p className="flex-1 text-sm leading-snug whitespace-pre-wrap break-words">
                                    {texto}
                                  </p>
                                  <Button
                                    type="button"
                                    variant="ghost"
                                    size="icon"
                                    className="shrink-0 h-9 w-9 text-muted-foreground hover:text-destructive"
                                    aria-label={`Remover comentário ${idx + 1}`}
                                    disabled={Boolean(quadroSaving[qk]) || data.status !== "finalizado"}
                                    onClick={() => void removerComentarioDaChave(qk, idx)}
                                  >
                                    <Trash2 className="h-4 w-4" aria-hidden />
                                  </Button>
                                </li>
                              ))}
                            </ul>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                    );
                  })}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <Dialog
        open={prazoModalQk !== null}
        onOpenChange={(open) => {
          if (!open) setPrazoModalQk(null);
        }}
      >
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Prazo planejado (meta)</DialogTitle>
            <DialogDescription>
              Informe a data no calendário e confirme para gravar no servidor (lock otimista If-Match). Deixe em
              branco e salve para limpar a meta.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2 py-1">
            <Label htmlFor="qdi-quadro-modal-prazo">Data (YYYY-MM-DD)</Label>
            <Input
              id="qdi-quadro-modal-prazo"
              type="date"
              className="h-10 bg-background"
              value={prazoModalDraft}
              onChange={(e) => setPrazoModalDraft(e.target.value)}
            />
          </div>
          <DialogFooter className="gap-2 sm:gap-0">
            <Button type="button" variant="outline" onClick={() => setPrazoModalQk(null)}>
              Cancelar
            </Button>
            <Button
              type="button"
              disabled={
                prazoModalQk != null ? Boolean(quadroSaving[prazoModalQk]) || data.status !== "finalizado" : true
              }
              onClick={() => void confirmarPrazoModal()}
            >
              {prazoModalQk != null && quadroSaving[prazoModalQk] ? "Gravando…" : "Salvar prazo"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog
        open={comentarioModalQk !== null}
        onOpenChange={(open) => {
          if (!open) {
            setComentarioModalQk(null);
            setComentarioModalDraft("");
          }
        }}
      >
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Novo comentário</DialogTitle>
            <DialogDescription>
              Registre follow-up ou observação para esta ação. Ao salvar, o comentário é persistido no servidor.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2 py-1">
            <Label htmlFor="qdi-quadro-modal-comentario">Texto</Label>
            <textarea
              id="qdi-quadro-modal-comentario"
              rows={4}
              className="w-full min-h-[6rem] rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              placeholder="Nota de implantação, responsável, dependência…"
              value={comentarioModalDraft}
              onChange={(e) => setComentarioModalDraft(e.target.value)}
            />
          </div>
          <DialogFooter className="gap-2 sm:gap-0">
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                setComentarioModalQk(null);
                setComentarioModalDraft("");
              }}
            >
              Cancelar
            </Button>
            <Button
              type="button"
              disabled={
                comentarioModalQk != null
                  ? Boolean(quadroSaving[comentarioModalQk]) || data.status !== "finalizado"
                  : true
              }
              onClick={() => void confirmarComentarioModal()}
            >
              {comentarioModalQk != null && quadroSaving[comentarioModalQk]
                ? "Gravando…"
                : "Salvar comentário"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog
        open={acaoEditModalQk !== null}
        onOpenChange={(open) => {
          if (!open) {
            setAcaoEditModalQk(null);
            setAcaoEditModalDraft("");
          }
        }}
      >
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>Alterar ação</DialogTitle>
            <DialogDescription>
              Texto exibido no título do cartão. Deixe em branco para voltar ao texto sugerido pelo motor.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2 py-1">
            <Label htmlFor="qdi-quadro-modal-desc-acao">Descrição da ação</Label>
            <textarea
              id="qdi-quadro-modal-desc-acao"
              rows={6}
              className="w-full min-h-[8rem] rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              placeholder="Deixe em branco para usar o texto sugerido pelo motor."
              value={acaoEditModalDraft}
              onChange={(e) => setAcaoEditModalDraft(e.target.value)}
            />
          </div>
          <DialogFooter className="gap-2 sm:gap-0">
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                setAcaoEditModalQk(null);
                setAcaoEditModalDraft("");
              }}
            >
              Cancelar
            </Button>
            <Button
              type="button"
              disabled={
                acaoEditModalQk != null
                  ? Boolean(quadroSaving[acaoEditModalQk]) || data.status !== "finalizado"
                  : true
              }
              onClick={() => void confirmarAcaoEditModal()}
            >
              {acaoEditModalQk != null && quadroSaving[acaoEditModalQk] ? "Gravando…" : "Salvar"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog
        open={m12ModalIndex !== null}
        onOpenChange={(open) => {
          if (!open) {
            setM12ModalIndex(null);
            setM12ModalDraft(null);
          }
        }}
      >
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Controle M12 — escala Likert</DialogTitle>
            <DialogDescription>
              Escolha obrigatória: 1 = não implementado, 5 = implementado e monitorado. «Aplicar» atualiza só este
              controle no ecrã; a persistência na base faz-se com «Gravar autoconf na API» quando os 10 estiverem
              assinalados.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2 py-2" role="radiogroup" aria-label="Escala Likert 1 a 5">
            {([1, 2, 3, 4, 5] as const).map((n) => (
              <label
                key={n}
                className={`flex cursor-pointer items-start gap-3 rounded-md border px-3 py-2 text-sm transition-colors ${
                  m12ModalDraft === n ? "border-primary bg-primary/5" : "border-border hover:bg-muted/40"
                }`}
              >
                <input
                  type="radio"
                  name="m12-likert"
                  className="mt-0.5"
                  checked={m12ModalDraft === n}
                  onChange={() => setM12ModalDraft(n)}
                />
                <span>
                  <span className="font-semibold text-foreground">{n}</span> — {rotuloLikertM12(n)}
                </span>
              </label>
            ))}
          </div>
          <DialogFooter className="gap-2 sm:gap-0">
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                setM12ModalIndex(null);
                setM12ModalDraft(null);
              }}
            >
              Cancelar
            </Button>
            <Button
              type="button"
              disabled={m12ModalDraft === null || data.status !== "finalizado"}
              onClick={() => confirmarM12Modal()}
            >
              Aplicar ao controle
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
