"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PlanoAcaoAcoesMenu } from "@/components/painel/empresa/PlanoAcaoAcoesMenu";
import { buildPlanoAcaoFichaHref } from "@/lib/dashboard/plano_acao_ficha_urls";
import {
  cabecalhosAuthPainelOpcional,
  getApiUrlForFetch,
  temSessaoPainelParaApiCliente,
} from "@/lib/api/config";
import { cn } from "@/lib/utils";
import { encerrarSessaoPainelSe401 } from "@/lib/auth/painel_session";
import { labelStatusExecucao } from "@/lib/painel/status_execucao_labels";
import {
  chavesQuadroIniciais,
  defaultQuadroEdicaoAcao,
  formatarMetaPrazoPtBr,
  linhasQuadroGrid,
  type QuadroEdicaoAcao,
} from "@/lib/painel/quadro_implantacao_utils";
import type { DiagnosticoDetalheApi } from "@/types/diagnostico_detalhe";
import type { PlanoAcaoKanbanCardApi } from "@/types/plano_acao_kanban";

type Props = {
  diagnosticoId: string;
  cnpj14: string;
  razaoSocial?: string;
  /** Cards do Kanban indexados por `plano_acao_id` — sincronização de leitura na grelha. */
  cardsPorPlanoId?: Record<string, PlanoAcaoKanbanCardApi>;
  data: DiagnosticoDetalheApi;
  editavel: boolean;
  avisoSomenteLeitura?: string;
  onDataAtualizado?: (d: DiagnosticoDetalheApi) => void;
  id?: string;
  /** Classes Tailwind opcionais no cartão raiz (ex.: margem na vista empresa). */
  className?: string;
};

function planoAcaoIdDaLinha(acao: { plano_acao_id?: string }, qk: string): string | null {
  const pid = (acao.plano_acao_id ?? "").trim();
  if (pid.length >= 32 && /^[0-9a-f-]+$/i.test(pid)) return pid;
  if (qk.length >= 32 && /^[0-9a-f-]+$/i.test(qk)) return qk;
  return null;
}

/** Quadro de implantação em grelha — âmbito empresa (quadro único por CNPJ no tenant). */
export function QuadroImplantacaoGrid({
  diagnosticoId,
  cnpj14,
  razaoSocial,
  cardsPorPlanoId = {},
  data,
  editavel,
  avisoSomenteLeitura,
  onDataAtualizado,
  id = "empresa-quadro-implantacao",
  className,
}: Props) {
  const versaoOtimistaRef = useRef<number | null>(data.versao_otimista ?? null);
  const [localData, setLocalData] = useState(data);
  const [quadroEdits, setQuadroEdits] = useState<Record<string, QuadroEdicaoAcao>>({});

  useEffect(() => {
    setLocalData(data);
    if (data.versao_otimista != null) versaoOtimistaRef.current = data.versao_otimista;
  }, [data]);

  useEffect(() => {
    if (!localData.checklist) return;
    setQuadroEdits(chavesQuadroIniciais(localData.checklist, localData.quadro_implantacao_anotacoes));
  }, [localData.id, localData.checklist, localData.quadro_implantacao_anotacoes]);

  const refetchDetalhe = useCallback(async () => {
    const base = getApiUrlForFetch().replace(/\/$/, "");
    const res = await fetch(`${base}/diagnosticos/${diagnosticoId}`, {
      headers: { Accept: "application/json", ...cabecalhosAuthPainelOpcional() },
      cache: "no-store",
      credentials: "include",
    });
    if (!res.ok) {
      if (encerrarSessaoPainelSe401(res.status)) return;
      return;
    }
    const json = (await res.json()) as DiagnosticoDetalheApi;
    if (json.versao_otimista != null) versaoOtimistaRef.current = json.versao_otimista;
    setLocalData(json);
    onDataAtualizado?.(json);
  }, [diagnosticoId, onDataAtualizado]);

  const linhas = linhasQuadroGrid(localData.checklist);
  const mostrarOperacoes = localData.status === "finalizado";

  return (
    <Card id={id} className={cn("scroll-mt-24", className)}>
      <CardHeader>
        <CardTitle className="text-base">Quadro de implantação da empresa</CardTitle>
        <p className="text-sm font-normal text-muted-foreground">
          Visão consolidada alinhada ao Kanban. Use <strong className="font-medium text-foreground">Ações</strong>{" "}
          ou clique no título para abrir a ficha unificada (planejamento + execução operacional).
        </p>
        {!editavel && avisoSomenteLeitura ? (
          <p className="text-sm border rounded-md p-3 mt-2 bg-amber-500/10 text-amber-900 dark:text-amber-200" role="note">
            {avisoSomenteLeitura}
          </p>
        ) : null}
      </CardHeader>
      <CardContent className="overflow-x-auto">
        {!linhas.length ? (
          <p className="text-sm text-muted-foreground border rounded-md p-4 bg-muted/20" role="status">
            O plano de implantação ainda não tem linhas materializadas neste ciclo de referência. Se o
            diagnóstico baseline já está <strong className="font-medium text-foreground">finalizado</strong>,
            aguarde a sincronização do checklist ou recarregue a página; ciclos só em andamento não geram
            grelha editável.
          </p>
        ) : null}
        {linhas.length > 0 ? (
        <table className="w-full text-sm border-collapse min-w-[960px]">
          <thead>
            <tr className="border-b bg-muted/30">
              <th className="text-center py-2 px-2 font-semibold w-12 tabular-nums">Seq.</th>
              <th className="text-left py-2 px-2 font-semibold">Frente</th>
              <th className="text-left py-2 px-2 font-semibold min-w-[200px]">Ação</th>
              <th className="text-left py-2 px-2 font-semibold">Responsável</th>
              <th className="text-left py-2 px-2 font-semibold">Criticidade</th>
              <th className="text-left py-2 px-2 font-semibold">Status oper.</th>
              <th className="text-left py-2 px-2 font-semibold">Prazo meta</th>
              <th className="text-left py-2 px-2 font-semibold">Prazo oper.</th>
              <th className="text-left py-2 px-2 font-semibold min-w-[100px]">Coment.</th>
              {mostrarOperacoes ? (
                <th className="text-left py-2 px-2 font-semibold w-[7.5rem]">Operações</th>
              ) : null}
            </tr>
          </thead>
          <tbody>
            {linhas.map(({ frente, acao, qk, sequencia }) => {
              const qv = quadroEdits[qk] ?? defaultQuadroEdicaoAcao();
              const titulo = (qv.descricao_personalizada || "").trim() || acao.descricao;
              const pid = planoAcaoIdDaLinha(acao, qk);
              const card = pid ? cardsPorPlanoId[pid] : undefined;
              const fichaHref =
                pid && mostrarOperacoes
                  ? buildPlanoAcaoFichaHref(cnpj14, pid, {
                      diagnosticoId,
                      razaoSocial,
                    })
                  : null;
              return (
                <tr key={qk} className="border-b border-muted/80 align-top">
                  <td className="py-3 px-2 text-center text-xs font-semibold tabular-nums text-muted-foreground">
                    {sequencia}
                  </td>
                  <td className="py-3 px-2 text-xs text-muted-foreground max-w-[8rem]">{frente}</td>
                  <td className="py-3 px-2">
                    {fichaHref ? (
                      <Link
                        href={fichaHref}
                        className="font-medium leading-snug text-primary hover:underline block"
                      >
                        {titulo}
                      </Link>
                    ) : (
                      <p className="font-medium leading-snug">{titulo}</p>
                    )}
                    {qv.descricao_personalizada.trim() ? (
                      <p className="text-xs text-muted-foreground mt-1">Motor: {acao.descricao}</p>
                    ) : null}
                    {acao.base_legal ? (
                      <p className="text-xs text-muted-foreground mt-0.5">{acao.base_legal}</p>
                    ) : null}
                  </td>
                  <td className="py-3 px-2 text-xs">
                    {card?.responsavel_operacional?.trim() ||
                      card?.responsavel_sugerido?.trim() ||
                      acao.responsavel ||
                      "—"}
                  </td>
                  <td className="py-3 px-2">
                    <Badge
                      variant={acao.criticidade === "Crítica" ? "destructive" : "secondary"}
                      className="text-[10px]"
                    >
                      {acao.criticidade}
                    </Badge>
                  </td>
                  <td className="py-3 px-2 text-xs">
                    {card ? (
                      <Badge variant="outline" className="text-[10px] font-normal">
                        {labelStatusExecucao(card.status_execucao)}
                      </Badge>
                    ) : (
                      <span className="text-muted-foreground">—</span>
                    )}
                  </td>
                  <td className="py-3 px-2 text-xs tabular-nums">
                    {qv.prazo_meta.trim() ? formatarMetaPrazoPtBr(qv.prazo_meta) : "—"}
                  </td>
                  <td className="py-3 px-2 text-xs tabular-nums">
                    {card?.prazo_operacional
                      ? formatarMetaPrazoPtBr(card.prazo_operacional)
                      : "—"}
                  </td>
                  <td className="py-3 px-2 text-xs tabular-nums text-muted-foreground">
                    {card?.comentarios_total ?? (qv.comentarios.length > 0 ? qv.comentarios.length : "—")}
                  </td>
                  {mostrarOperacoes && pid ? (
                    <td className="py-3 px-2">
                      <PlanoAcaoAcoesMenu
                        cnpj14={cnpj14}
                        diagnosticoId={diagnosticoId}
                        planoAcaoId={pid}
                        razaoSocial={razaoSocial}
                        disabled={!editavel}
                      />
                    </td>
                  ) : mostrarOperacoes ? (
                    <td className="py-3 px-2 text-xs text-muted-foreground">—</td>
                  ) : null}
                </tr>
              );
            })}
          </tbody>
        </table>
        ) : null}
      </CardContent>
    </Card>
  );
}
