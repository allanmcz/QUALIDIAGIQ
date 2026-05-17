"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { fetchDiagnosticoDetalhe } from "@/lib/api/fetch_diagnostico_detalhe";
import { temSessaoPainelParaApiCliente } from "@/lib/api/config";
import {
  adicionarComentarioKanban,
  arquivarKanbanCard,
  atualizarEstadoKanbanCard,
  buscarKanbanPlanoAcao,
  listarComentariosKanban,
} from "@/lib/api/plano_acao_kanban";
import { buildVoltaEmpresaHref } from "@/lib/dashboard/plano_acao_ficha_urls";
import { quadroImplantacaoEditavel } from "@/lib/painel/diagnostico_empresa_ordem";
import { salvarQuadroAcao } from "@/lib/painel/salvar_quadro_acao";
import { labelStatusExecucao } from "@/lib/painel/status_execucao_labels";
import {
  chaveQuadroParaAcao,
  chavesQuadroIniciais,
  defaultQuadroEdicaoAcao,
  formatarMetaPrazoPtBr,
  limparSufixoLacunaScoreAcao,
  resolverChaveQuadroSalvar,
  type QuadroEdicaoAcao,
} from "@/lib/painel/quadro_implantacao_utils";
import type { DiagnosticoResumoApi } from "@/lib/api/lista_diagnosticos";
import type { AcaoChecklistDetalhe } from "@/types/diagnostico_detalhe";
import type { PlanoAcaoComentarioApi, PlanoAcaoKanbanCardApi, StatusExecucaoPlanoAcao } from "@/types/plano_acao_kanban";

function mascaraCnpj14(d: string): string {
  const c = d.replace(/\D/g, "");
  if (c.length !== 14) return d;
  return c.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/, "$1.$2.$3/$4-$5");
}

function acharAcaoChecklist(
  detalhe: Awaited<ReturnType<typeof fetchDiagnosticoDetalhe>> | null,
  planoAcaoId: string,
  card: PlanoAcaoKanbanCardApi | null,
): { acao: AcaoChecklistDetalhe; chaveQuadro: string } | null {
  if (!detalhe?.checklist) return null;
  for (let i = 0; i < detalhe.checklist.length; i++) {
    const frente = detalhe.checklist[i]!;
    for (let j = 0; j < frente.acoes.length; j++) {
      const acao = frente.acoes[j]!;
      const pid = (acao.plano_acao_id ?? "").trim();
      const bateId = pid === planoAcaoId;
      const bateIndice =
        card != null && card.frente_indice === i && card.acao_indice === j;
      if (bateId || bateIndice) {
        return {
          acao,
          chaveQuadro: chaveQuadroParaAcao(
            {
              descricao: acao.descricao,
              responsavel: acao.responsavel,
              prazo: acao.prazo,
              criticidade: acao.criticidade,
              plano_acao_id: acao.plano_acao_id,
              chave_quadro_legado: acao.chave_quadro_legado,
            },
            i,
            j,
          ),
        };
      }
    }
  }
  return null;
}

type Props = {
  cnpj14: string;
  planoAcaoId: string;
  diagnosticoId: string;
  razaoSocialHint: string;
  listaPainel: DiagnosticoResumoApi[] | null;
};

export function PlanoAcaoFichaUnificadaClient({
  cnpj14,
  planoAcaoId,
  diagnosticoId,
  razaoSocialHint,
  listaPainel,
}: Props) {
  const router = useRouter();
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [msgTipo, setMsgTipo] = useState<"erro" | "aviso" | "sucesso">("aviso");
  const [salvando, setSalvando] = useState(false);

  const [detalhe, setDetalhe] = useState<Awaited<ReturnType<typeof fetchDiagnosticoDetalhe>> | null>(
    null,
  );
  const [card, setCard] = useState<PlanoAcaoKanbanCardApi | null>(null);
  const [comentarios, setComentarios] = useState<PlanoAcaoComentarioApi[]>([]);

  const [quadroEdicao, setQuadroEdicao] = useState<QuadroEdicaoAcao>(defaultQuadroEdicaoAcao());
  const [status, setStatus] = useState<StatusExecucaoPlanoAcao>("pendente");
  const [responsavelOp, setResponsavelOp] = useState("");
  const [prazoOp, setPrazoOp] = useState("");
  const [bloqueio, setBloqueio] = useState("");
  const [descricaoOp, setDescricaoOp] = useState("");
  const [novoComentario, setNovoComentario] = useState("");

  const acaoCtx = useMemo(
    () => acharAcaoChecklist(detalhe, planoAcaoId, card),
    [detalhe, planoAcaoId, card],
  );

  const chaveQuadroSalvar = useMemo(
    () =>
      resolverChaveQuadroSalvar({
        planoAcaoId,
        chaveDeAcaoCtx: acaoCtx?.chaveQuadro,
        chaveQuadroLegado: card?.chave_quadro_legado,
      }),
    [planoAcaoId, acaoCtx?.chaveQuadro, card?.chave_quadro_legado],
  );

  const editavel = useMemo(() => {
    if (!detalhe) return false;
    return quadroImplantacaoEditavel(detalhe.id, listaPainel ?? [], detalhe.status);
  }, [detalhe, listaPainel]);

  const tituloExibido = useMemo(() => {
    const custom = quadroEdicao.descricao_personalizada.trim();
    if (custom) return custom;
    const canonico = card?.texto_acao ?? acaoCtx?.acao.descricao ?? "";
    return limparSufixoLacunaScoreAcao(canonico) || "Ação do plano";
  }, [quadroEdicao.descricao_personalizada, card, acaoCtx]);

  const voltaHref = buildVoltaEmpresaHref(cnpj14, razaoSocialHint, "empresa-quadro-implantacao-principal");

  const carregar = useCallback(async () => {
    if (!temSessaoPainelParaApiCliente()) {
      setErro("Sessão necessária — faça login na plataforma.");
      setCarregando(false);
      return;
    }
    setCarregando(true);
    setErro(null);
    try {
      const [d, board] = await Promise.all([
        fetchDiagnosticoDetalhe(diagnosticoId),
        buscarKanbanPlanoAcao(diagnosticoId, { incluirArquivados: true }),
      ]);
      setDetalhe(d);
      const encontrado = board?.cards.find((c) => c.plano_acao_id === planoAcaoId) ?? null;
      if (!encontrado) {
        setErro("Ação não encontrada no Kanban deste ciclo de referência.");
        setCard(null);
        return;
      }
      setCard(encontrado);
      setStatus(encontrado.status_execucao);
      setResponsavelOp(encontrado.responsavel_operacional ?? "");
      setPrazoOp(encontrado.prazo_operacional ?? "");
      setBloqueio(encontrado.bloqueio_motivo ?? "");
      setDescricaoOp(encontrado.descricao_operacional ?? "");

      const ctx = acharAcaoChecklist(d, planoAcaoId, encontrado);
      const chave = resolverChaveQuadroSalvar({
        planoAcaoId,
        chaveDeAcaoCtx: ctx?.chaveQuadro,
        chaveQuadroLegado: encontrado.chave_quadro_legado,
      });
      if (chave && d.checklist) {
        const mapa = chavesQuadroIniciais(d.checklist, d.quadro_implantacao_anotacoes);
        setQuadroEdicao(mapa[chave] ?? mapa[encontrado.chave_quadro_legado] ?? defaultQuadroEdicaoAcao());
      }

      const coms = await listarComentariosKanban(diagnosticoId, planoAcaoId);
      setComentarios(coms);
    } catch (e) {
      setErro(e instanceof Error ? e.message : "Falha ao carregar a ficha da ação.");
    } finally {
      setCarregando(false);
    }
  }, [diagnosticoId, listaPainel, planoAcaoId]);

  useEffect(() => {
    void carregar();
  }, [carregar]);

  /** Ao abrir ou trocar de ação, mostra o cabeçalho da ficha (não herda scroll da página anterior). */
  useEffect(() => {
    if (typeof window === "undefined") return;
    window.scrollTo({ top: 0, left: 0, behavior: "instant" });
  }, [planoAcaoId, diagnosticoId]);

  useEffect(() => {
    if (carregando || typeof window === "undefined") return;
    window.scrollTo({ top: 0, left: 0, behavior: "instant" });
  }, [carregando, planoAcaoId]);

  const exibirMsg = (texto: string, tipo: "erro" | "aviso" | "sucesso" = "aviso") => {
    setMsgTipo(tipo);
    setMsg(texto);
    requestAnimationFrame(() => {
      document.getElementById("ficha-acao-feedback")?.scrollIntoView({ behavior: "smooth", block: "nearest" });
    });
  };

  const salvarTudo = async () => {
    if (!detalhe || !card) {
      exibirMsg("Dados da ação incompletos — recarregue a página.", "erro");
      return;
    }
    if (!editavel) {
      exibirMsg("Este quadro está em modo somente leitura.", "aviso");
      return;
    }
    if (!chaveQuadroSalvar) {
      exibirMsg(
        "Não foi possível identificar a chave do quadro para gravar o planejamento. Recarregue ou contacte o suporte.",
        "erro",
      );
      return;
    }
    const v = detalhe.versao_otimista;
    if (v == null) {
      exibirMsg("Versão otimista indisponível — recarregue a página.", "erro");
      return;
    }
    setSalvando(true);
    setMsg(null);
    try {
      const quadroResult = await salvarQuadroAcao(
        diagnosticoId,
        chaveQuadroSalvar,
        quadroEdicao,
        v,
      );
      if (!quadroResult.ok) {
        if (quadroResult.conflitoVersao) await carregar();
        exibirMsg(quadroResult.mensagem, "erro");
        return;
      }
      setDetalhe(quadroResult.detalhe);

      const cardAtualizado = await atualizarEstadoKanbanCard(diagnosticoId, planoAcaoId, {
        status_execucao: status,
        responsavel_operacional: responsavelOp.trim() || null,
        prazo_operacional: prazoOp.trim() || null,
        limpar_prazo: !prazoOp.trim(),
        bloqueio_motivo: status === "bloqueado" ? bloqueio.trim() || null : null,
        limpar_bloqueio: status !== "bloqueado",
        descricao_operacional: descricaoOp.trim() || null,
      });
      setCard(cardAtualizado);

      if (novoComentario.trim()) {
        await adicionarComentarioKanban(diagnosticoId, planoAcaoId, novoComentario.trim());
        setNovoComentario("");
      }

      router.push(
        buildVoltaEmpresaHref(cnpj14, razaoSocialHint, "empresa-quadro-implantacao-principal", {
          fichaSalva: true,
        }),
      );
    } catch (e) {
      exibirMsg(e instanceof Error ? e.message : "Falha ao gravar.", "erro");
    } finally {
      setSalvando(false);
    }
  };

  const toggleArquivar = async () => {
    if (!editavel || !card) return;
    setSalvando(true);
    try {
      await arquivarKanbanCard(diagnosticoId, planoAcaoId, !card.arquivado);
      router.push(voltaHref);
    } catch (e) {
      exibirMsg(e instanceof Error ? e.message : "Falha ao arquivar.", "erro");
    } finally {
      setSalvando(false);
    }
  };

  if (carregando) {
    return (
      <div className="container py-10 text-muted-foreground" role="status">
        A carregar ficha da ação…
      </div>
    );
  }

  if (erro || !card) {
    return (
      <div className="container py-10 space-y-4">
        <Link href={voltaHref} className="text-sm text-primary hover:underline">
          ← Voltar à implantação da empresa
        </Link>
        <p className="text-destructive" role="alert">
          {erro ?? "Ação não disponível."}
        </p>
      </div>
    );
  }

  return (
    <div className="container max-w-4xl pb-10 pt-6">
      <div className="flex flex-col gap-6">
        <header
          id="ficha-acao-cabecalho"
          className="sticky top-16 z-30 -mx-4 border-b border-border/60 bg-slate-50/95 px-4 py-4 backdrop-blur-sm supports-[backdrop-filter]:bg-slate-50/85"
        >
          <div className="space-y-2">
            <Link href={voltaHref} className="text-sm text-primary hover:underline inline-block">
              ← Voltar à implantação da empresa
            </Link>
            <div className="flex flex-wrap items-start gap-2">
              <Badge variant="outline" className="tabular-nums">
                #{card.ordem_kanban + 1}
              </Badge>
              <Badge variant="secondary">{labelStatusExecucao(card.status_execucao)}</Badge>
              {card.arquivado ? <Badge variant="outline">Arquivado</Badge> : null}
            </div>
            <h1 className="text-2xl font-bold tracking-tight">{tituloExibido}</h1>
            <p className="text-sm text-muted-foreground">
              {card.frente_nome}
              {razaoSocialHint ? ` · ${razaoSocialHint}` : ""} · CNPJ {mascaraCnpj14(cnpj14)}
            </p>
          </div>
        </header>

        {msg ? (
          <p
            id="ficha-acao-feedback"
            className={
              msgTipo === "erro"
                ? "text-sm border rounded-md p-3 border-destructive/40 bg-destructive/10 text-destructive"
                : msgTipo === "sucesso"
                  ? "text-sm border rounded-md p-3 border-emerald-600/40 bg-emerald-500/10 text-emerald-900 dark:text-emerald-200"
                  : "text-sm border rounded-md p-3 bg-amber-500/10 border-amber-600/30 text-amber-950 dark:text-amber-100"
            }
            role={msgTipo === "erro" ? "alert" : "status"}
          >
            {msg}
          </p>
        ) : null}

        <Card>
          <CardContent className="space-y-2 text-sm pt-6">
            <p>{limparSufixoLacunaScoreAcao(card.texto_acao)}</p>
            {card.base_legal ? (
              <p className="text-muted-foreground text-xs">Base legal: {card.base_legal}</p>
            ) : null}
            <div className="flex flex-wrap gap-2">
              {card.criticidade ? <Badge variant="outline">{card.criticidade}</Badge> : null}
              {card.fase_pdca ? <Badge variant="secondary">PDCA {card.fase_pdca}</Badge> : null}
              {card.horizonte_planejado ? (
                <span className="text-xs text-muted-foreground">Horizonte: {card.horizonte_planejado}</span>
              ) : null}
            </div>
            {card.responsavel_sugerido ? (
              <p className="text-xs">Responsável sugerido: {card.responsavel_sugerido}</p>
            ) : null}
            {acaoCtx?.acao.subtarefas?.length ? (
              <div>
                <p className="font-medium mt-2">Subtarefas ({acaoCtx.acao.subtarefas.length})</p>
                <ul className="list-disc pl-5 text-muted-foreground">
                  {acaoCtx.acao.subtarefas.map((s) => (
                    <li key={s.id}>
                      {s.titulo} — {s.status}
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Planejamento (quadro da empresa)</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1 sm:col-span-2">
              <Label htmlFor="titulo-exibido">Título exibido</Label>
              <Input
                id="titulo-exibido"
                value={quadroEdicao.descricao_personalizada}
                onChange={(e) =>
                  setQuadroEdicao((q) => ({ ...q, descricao_personalizada: e.target.value }))
                }
                disabled={!editavel}
                placeholder={limparSufixoLacunaScoreAcao(card.texto_acao)}
              />
            </div>
            <div className="space-y-1">
              <Label htmlFor="prazo-meta">Prazo meta</Label>
              <Input
                id="prazo-meta"
                type="date"
                value={quadroEdicao.prazo_meta}
                onChange={(e) => setQuadroEdicao((q) => ({ ...q, prazo_meta: e.target.value }))}
                disabled={!editavel}
              />
              {quadroEdicao.prazo_meta ? (
                <p className="text-xs text-muted-foreground">
                  {formatarMetaPrazoPtBr(quadroEdicao.prazo_meta)}
                </p>
              ) : null}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Execução operacional (Kanban)</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 sm:grid-cols-2">
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
              <Label htmlFor="resp-op">Responsável operacional</Label>
              <Input
                id="resp-op"
                value={responsavelOp}
                onChange={(e) => setResponsavelOp(e.target.value)}
                disabled={!editavel}
              />
            </div>
            <div className="space-y-1">
              <Label htmlFor="prazo-op">Prazo operacional</Label>
              <Input
                id="prazo-op"
                type="date"
                value={prazoOp}
                onChange={(e) => setPrazoOp(e.target.value)}
                disabled={!editavel}
              />
            </div>
            {status === "bloqueado" ? (
              <div className="space-y-1 sm:col-span-2">
                <Label htmlFor="bloqueio">Motivo do bloqueio</Label>
                <textarea
                  id="bloqueio"
                  className="flex min-h-[72px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  value={bloqueio}
                  onChange={(e) => setBloqueio(e.target.value)}
                  disabled={!editavel}
                />
              </div>
            ) : null}
            <div className="space-y-1 sm:col-span-2">
              <Label htmlFor="notas-op">Notas operacionais</Label>
              <textarea
                id="notas-op"
                className="flex min-h-[72px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                value={descricaoOp}
                onChange={(e) => setDescricaoOp(e.target.value)}
                disabled={!editavel}
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Comentários auditáveis</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <ul className="space-y-2 max-h-56 overflow-y-auto">
              {comentarios.length === 0 ? (
                <li className="text-sm text-muted-foreground">Nenhum comentário ainda.</li>
              ) : (
                comentarios.map((c) => (
                  <li key={c.id} className="rounded-md border p-3 text-sm">
                    <span className="font-medium">{c.autor_label}</span>
                    <span className="text-muted-foreground text-xs ml-2">
                      {new Date(c.criado_em).toLocaleString("pt-BR")}
                    </span>
                    <p className="mt-1 whitespace-pre-wrap">{c.comentario}</p>
                  </li>
                ))
              )}
            </ul>
            {editavel ? (
              <div className="flex flex-col sm:flex-row gap-2">
                <textarea
                  value={novoComentario}
                  onChange={(e) => setNovoComentario(e.target.value)}
                  placeholder="Novo comentário (gravado ao salvar)"
                  rows={2}
                  className="flex min-h-[60px] flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm"
                />
              </div>
            ) : null}
            <p className="text-xs text-muted-foreground">
              Comentários legados só no quadro JSONB não são migrados automaticamente — use comentários
              auditáveis acima para o histórico oficial.
            </p>
          </CardContent>
        </Card>

        <div className="flex flex-wrap gap-2 justify-end border-t pt-4">
          <Button type="button" variant="outline" asChild>
            <Link href={voltaHref}>Cancelar</Link>
          </Button>
          {editavel ? (
            <>
              <Button type="button" variant="outline" onClick={() => void toggleArquivar()} disabled={salvando}>
                {card.arquivado ? "Restaurar card" : "Arquivar card"}
              </Button>
              <Button type="button" onClick={() => void salvarTudo()} disabled={salvando}>
                {salvando ? "A gravar…" : "Salvar alterações"}
              </Button>
            </>
          ) : null}
        </div>
      </div>
    </div>
  );
}
