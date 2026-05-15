"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { CalendarPlus, Pencil, Plus } from "lucide-react";

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
import {
  cabecalhosAuthPainelOpcional,
  getApiUrlForFetch,
  temSessaoPainelParaApiCliente,
} from "@/lib/api/config";
import { encerrarSessaoPainelSe401 } from "@/lib/auth/painel_session";
import {
  chavesQuadroIniciais,
  defaultQuadroEdicaoAcao,
  formatarMetaPrazoPtBr,
  linhasQuadroGrid,
  type QuadroEdicaoAcao,
} from "@/lib/painel/quadro_implantacao_utils";
import type { DiagnosticoDetalheApi } from "@/types/diagnostico_detalhe";

type Props = {
  diagnosticoId: string;
  data: DiagnosticoDetalheApi;
  editavel: boolean;
  avisoSomenteLeitura?: string;
  onDataAtualizado?: (d: DiagnosticoDetalheApi) => void;
  id?: string;
};

/** Quadro de implantação em grelha (painel empresa — expansão da linha). */
export function QuadroImplantacaoGrid({
  diagnosticoId,
  data,
  editavel,
  avisoSomenteLeitura,
  onDataAtualizado,
  id = "empresa-quadro-implantacao",
}: Props) {
  const versaoOtimistaRef = useRef<number | null>(data.versao_otimista ?? null);
  const [localData, setLocalData] = useState(data);
  const [quadroEdits, setQuadroEdits] = useState<Record<string, QuadroEdicaoAcao>>({});
  const [quadroSaving, setQuadroSaving] = useState<Record<string, boolean>>({});
  const [quadroMsgPorAcao, setQuadroMsgPorAcao] = useState<Record<string, string>>({});
  const [prazoModalQk, setPrazoModalQk] = useState<string | null>(null);
  const [prazoModalDraft, setPrazoModalDraft] = useState("");
  const [comentarioModalQk, setComentarioModalQk] = useState<string | null>(null);
  const [comentarioModalDraft, setComentarioModalDraft] = useState("");
  const [acaoEditModalQk, setAcaoEditModalQk] = useState<string | null>(null);
  const [acaoEditModalDraft, setAcaoEditModalDraft] = useState("");

  useEffect(() => {
    setLocalData(data);
    if (data.versao_otimista != null) versaoOtimistaRef.current = data.versao_otimista;
  }, [data]);

  useEffect(() => {
    if (!localData.checklist) return;
    setQuadroEdits(chavesQuadroIniciais(localData.checklist, localData.quadro_implantacao_anotacoes));
  }, [localData.id, localData.checklist, localData.quadro_implantacao_anotacoes]);

  useEffect(() => {
    setQuadroMsgPorAcao({});
  }, [localData.id]);

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

  const salvarQuadroAcao = useCallback(
    async (qk: string, snapshot?: Partial<QuadroEdicaoAcao>): Promise<boolean> => {
      if (!editavel) return false;
      if (!temSessaoPainelParaApiCliente() || localData.status !== "finalizado") {
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
      const body = {
        [qk]: {
          prazo_meta: qv.prazo_meta.trim(),
          comentarios: qv.comentarios.map((s) => s.trim()).filter(Boolean),
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
        const res = await fetch(`${base}/diagnosticos/${diagnosticoId}/quadro-implantacao-anotacoes`, {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
            Accept: "application/json",
            ...cabecalhosAuthPainelOpcional(),
            "If-Match": String(v),
          },
          credentials: "include",
          body: JSON.stringify({ quadro_implantacao_anotacoes: body }),
        });
        if (encerrarSessaoPainelSe401(res.status)) return false;
        if (res.ok) {
          const json = (await res.json()) as DiagnosticoDetalheApi;
          if (json.versao_otimista != null) versaoOtimistaRef.current = json.versao_otimista;
          setLocalData(json);
          onDataAtualizado?.(json);
          setQuadroMsgPorAcao((prev) => ({ ...prev, [qk]: "Ação gravada." }));
          return true;
        }
        if (res.status === 412) {
          setQuadroMsgPorAcao((prev) => ({ ...prev, [qk]: "Conflito de versão — recarregando…" }));
          await refetchDetalhe();
          return false;
        }
        const t = await res.text();
        setQuadroMsgPorAcao((prev) => ({
          ...prev,
          [qk]: `Não foi possível gravar (${res.status}): ${t.slice(0, 120)}`,
        }));
        return false;
      } catch {
        setQuadroMsgPorAcao((prev) => ({ ...prev, [qk]: "Falha de rede ao gravar." }));
        return false;
      } finally {
        setQuadroSaving((s) => ({ ...s, [qk]: false }));
      }
    },
    [diagnosticoId, editavel, localData.status, onDataAtualizado, quadroEdits, refetchDetalhe],
  );

  const linhas = linhasQuadroGrid(localData.checklist);
  if (!linhas.length) return null;

  const podeEditarLinha = editavel && localData.status === "finalizado";

  return (
    <Card id={id} className="scroll-mt-24">
      <CardHeader>
        <CardTitle className="text-base">Quadro de implantação</CardTitle>
        <p className="text-sm font-normal text-muted-foreground">
          {editavel
            ? "Grelha de ações do plano — edição permitida neste primeiro diagnóstico da empresa (If-Match)."
            : "Visualização em grelha — o quadro só pode ser alterado no primeiro diagnóstico desta empresa."}
        </p>
        {!editavel && avisoSomenteLeitura ? (
          <p className="text-sm border rounded-md p-3 mt-2 bg-amber-500/10 text-amber-900 dark:text-amber-200" role="note">
            {avisoSomenteLeitura}
          </p>
        ) : null}
      </CardHeader>
      <CardContent className="overflow-x-auto">
        <table className="w-full text-sm border-collapse min-w-[960px]">
          <thead>
            <tr className="border-b bg-muted/30">
              <th className="text-left py-2 px-2 font-semibold">Frente</th>
              <th className="text-left py-2 px-2 font-semibold min-w-[200px]">Ação</th>
              <th className="text-left py-2 px-2 font-semibold">Responsável</th>
              <th className="text-left py-2 px-2 font-semibold">Criticidade</th>
              <th className="text-left py-2 px-2 font-semibold">Prazo motor</th>
              <th className="text-left py-2 px-2 font-semibold">Prazo meta</th>
              <th className="text-left py-2 px-2 font-semibold min-w-[140px]">Comentários</th>
              {podeEditarLinha ? (
                <th className="text-left py-2 px-2 font-semibold w-[11rem]">Operações</th>
              ) : null}
            </tr>
          </thead>
          <tbody>
            {linhas.map(({ frente, acao, qk }) => {
              const qv = quadroEdits[qk] ?? defaultQuadroEdicaoAcao();
              const titulo = (qv.descricao_personalizada || "").trim() || acao.descricao;
              return (
                <tr key={qk} className="border-b border-muted/80 align-top">
                  <td className="py-3 px-2 text-xs text-muted-foreground max-w-[8rem]">{frente}</td>
                  <td className="py-3 px-2">
                    <p className="font-medium leading-snug">{titulo}</p>
                    {qv.descricao_personalizada.trim() ? (
                      <p className="text-xs text-muted-foreground mt-1">Motor: {acao.descricao}</p>
                    ) : null}
                    {acao.base_legal ? (
                      <p className="text-xs text-muted-foreground mt-0.5">{acao.base_legal}</p>
                    ) : null}
                  </td>
                  <td className="py-3 px-2 text-xs">{acao.responsavel}</td>
                  <td className="py-3 px-2">
                    <Badge
                      variant={acao.criticidade === "Crítica" ? "destructive" : "secondary"}
                      className="text-[10px]"
                    >
                      {acao.criticidade}
                    </Badge>
                  </td>
                  <td className="py-3 px-2 text-xs text-muted-foreground">{acao.prazo}</td>
                  <td className="py-3 px-2 text-xs tabular-nums">
                    {qv.prazo_meta.trim()
                      ? formatarMetaPrazoPtBr(qv.prazo_meta)
                      : "—"}
                  </td>
                  <td className="py-3 px-2 text-xs">
                    {qv.comentarios.length === 0 ? (
                      <span className="text-muted-foreground">—</span>
                    ) : (
                      <ul className="list-disc pl-4 space-y-1 m-0">
                        {qv.comentarios.map((c, idx) => (
                          <li key={idx} className="leading-snug">
                            {c}
                          </li>
                        ))}
                      </ul>
                    )}
                  </td>
                  {podeEditarLinha ? (
                    <td className="py-3 px-2">
                      <div className="flex flex-col gap-1">
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          className="h-7 text-xs gap-1"
                          disabled={Boolean(quadroSaving[qk])}
                          onClick={() => {
                            setAcaoEditModalDraft(qv.descricao_personalizada ?? "");
                            setAcaoEditModalQk(qk);
                          }}
                        >
                          <Pencil className="h-3 w-3" aria-hidden />
                          Ação
                        </Button>
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          className="h-7 text-xs gap-1"
                          disabled={Boolean(quadroSaving[qk])}
                          onClick={() => {
                            setPrazoModalDraft(qv.prazo_meta);
                            setPrazoModalQk(qk);
                          }}
                        >
                          <CalendarPlus className="h-3 w-3" aria-hidden />
                          Prazo
                        </Button>
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          className="h-7 text-xs gap-1"
                          disabled={Boolean(quadroSaving[qk])}
                          onClick={() => {
                            setComentarioModalDraft("");
                            setComentarioModalQk(qk);
                          }}
                        >
                          <Plus className="h-3 w-3" aria-hidden />
                          Coment.
                        </Button>
                        {quadroMsgPorAcao[qk] ? (
                          <span className="text-[10px] text-muted-foreground" role="status">
                            {quadroMsgPorAcao[qk]}
                          </span>
                        ) : null}
                      </div>
                    </td>
                  ) : null}
                </tr>
              );
            })}
          </tbody>
        </table>
      </CardContent>

      <Dialog open={prazoModalQk !== null} onOpenChange={(open) => !open && setPrazoModalQk(null)}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Prazo planejado (meta)</DialogTitle>
            <DialogDescription>Data YYYY-MM-DD — gravar com If-Match.</DialogDescription>
          </DialogHeader>
          <Input type="date" value={prazoModalDraft} onChange={(e) => setPrazoModalDraft(e.target.value)} />
          <DialogFooter>
            <Button variant="outline" onClick={() => setPrazoModalQk(null)}>
              Cancelar
            </Button>
            <Button
              onClick={() => {
                void salvarQuadroAcao(prazoModalQk!, { prazo_meta: prazoModalDraft.trim() }).then((ok) => {
                  if (ok) setPrazoModalQk(null);
                });
              }}
            >
              Gravar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={comentarioModalQk !== null} onOpenChange={(open) => !open && setComentarioModalQk(null)}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Comentário</DialogTitle>
          </DialogHeader>
          <textarea
            className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            value={comentarioModalDraft}
            onChange={(e) => setComentarioModalDraft(e.target.value)}
          />
          <DialogFooter>
            <Button variant="outline" onClick={() => setComentarioModalQk(null)}>
              Cancelar
            </Button>
            <Button
              onClick={() => {
                const qk = comentarioModalQk!;
                const t = comentarioModalDraft.trim();
                if (!t) {
                  setComentarioModalQk(null);
                  return;
                }
                const cur = { ...defaultQuadroEdicaoAcao(), ...quadroEdits[qk] };
                void salvarQuadroAcao(qk, { comentarios: [...cur.comentarios, t] }).then((ok) => {
                  if (ok) {
                    setComentarioModalQk(null);
                    setComentarioModalDraft("");
                  }
                });
              }}
            >
              Gravar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={acaoEditModalQk !== null} onOpenChange={(open) => !open && setAcaoEditModalQk(null)}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Alterar texto da ação</DialogTitle>
          </DialogHeader>
          <textarea
            className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            value={acaoEditModalDraft}
            onChange={(e) => setAcaoEditModalDraft(e.target.value)}
          />
          <DialogFooter>
            <Button variant="outline" onClick={() => setAcaoEditModalQk(null)}>
              Cancelar
            </Button>
            <Button
              onClick={() => {
                void salvarQuadroAcao(acaoEditModalQk!, {
                  descricao_personalizada: acaoEditModalDraft.trim(),
                }).then((ok) => {
                  if (ok) setAcaoEditModalQk(null);
                });
              }}
            >
              Salvar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  );
}
