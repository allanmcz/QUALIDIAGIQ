"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import { PrivacidadeNovaSolicitacaoCard } from "@/components/painel/PrivacidadeNovaSolicitacaoCard";
import { RetificacaoDiagnosticoCard } from "@/components/painel/RetificacaoDiagnosticoCard";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { downloadBlob } from "@/lib/browser_download";
import {
  fetchExportPortabilidadeDiagnostico,
  fetchSolicitacoesLgpd,
  patchStatusSolicitacaoLgpd,
  postAnonimizarRespondenteLgpd,
  type FormatoExportPortabilidade,
  type SolicitacaoTitularLgpd,
} from "@/lib/api/privacidade_lgpd";
import type { DiagnosticoResumoApi } from "@/lib/api/lista_diagnosticos";
import { mascaraCnpj14 } from "@/lib/painel/formatar_cnpj";
import type { EmpresaPrivacidadeIndice } from "@/lib/painel/privacidade_empresa_indice";
import {
  hrefPrivacidadePainel,
  PRIVACIDADE_QUERY_DIAGNOSTICO_ID,
  PRIVACIDADE_QUERY_SECAO,
  parseSecaoPrivacidade,
} from "@/lib/painel/privacidade_diagnostico_query";

const ROTULO_TIPO: Record<string, string> = {
  acesso: "Acesso",
  correcao: "Correção",
  anonimizacao: "Anonimização",
  eliminacao: "Eliminação",
  portabilidade: "Portabilidade",
  oposicao: "Oposição",
};

const ROTULO_STATUS: Record<string, string> = {
  recebida: "Recebida",
  em_analise: "Em análise",
  deferida: "Deferida",
  indeferida: "Indeferida",
  concluida: "Concluída",
};

const STATUS_OPCOES = ["recebida", "em_analise", "deferida", "indeferida", "concluida"] as const;

export function DashboardPrivacidadeClient() {
  const searchParams = useSearchParams();
  const diagnosticoIdInicial = searchParams.get(PRIVACIDADE_QUERY_DIAGNOSTICO_ID)?.trim() ?? "";

  const [empresaFiltro, setEmpresaFiltro] = useState<EmpresaPrivacidadeIndice | null>(null);
  const [filtrarSoEmpresa, setFiltrarSoEmpresa] = useState(false);
  const [diagUnicoRetif, setDiagUnicoRetif] = useState<DiagnosticoResumoApi | null>(null);

  const [linhas, setLinhas] = useState<SolicitacaoTitularLgpd[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);
  const [filtroStatus, setFiltroStatus] = useState<string>("");
  const [pendentesPatch, setPendentesPatch] = useState<Record<string, string>>({});
  const [salvandoId, setSalvandoId] = useState<string | null>(null);
  const [execId, setExecId] = useState<string | null>(null);
  const [msgGlobal, setMsgGlobal] = useState<string | null>(null);
  const [exportandoChave, setExportandoChave] = useState<string | null>(null);
  const [diagIdsEmpresa, setDiagIdsEmpresa] = useState<Set<string>>(new Set());

  useEffect(() => {
    const secao = parseSecaoPrivacidade(searchParams.get(PRIVACIDADE_QUERY_SECAO));
    const alvo =
      secao === "retificacoes"
        ? "priv-retificacoes"
        : secao === "lgpd"
          ? "priv-lgpd-registrar"
          : null;
    if (!alvo) return;
    const t = window.setTimeout(() => {
      document.getElementById(alvo)?.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 150);
    return () => window.clearTimeout(t);
  }, [searchParams]);

  const recarregar = useCallback(async () => {
    setCarregando(true);
    setErro(null);
    try {
      const dados = await fetchSolicitacoesLgpd({
        limit: 200,
        status: filtroStatus.trim() || undefined,
      });
      setLinhas(dados);
    } catch (e) {
      setErro(e instanceof Error ? e.message : "Falha ao carregar.");
      setLinhas([]);
    } finally {
      setCarregando(false);
    }
  }, [filtroStatus]);

  useEffect(() => {
    void recarregar();
  }, [recarregar]);

  const linhasFiltradas = useMemo(() => {
    if (!filtrarSoEmpresa || !empresaFiltro || diagIdsEmpresa.size === 0) return linhas;
    return linhas.filter(
      (row) => row.diagnostico_id != null && diagIdsEmpresa.has(String(row.diagnostico_id)),
    );
  }, [linhas, filtrarSoEmpresa, empresaFiltro, diagIdsEmpresa]);

  const aplicarStatus = async (row: SolicitacaoTitularLgpd) => {
    const novo = pendentesPatch[row.id] ?? row.status;
    if (novo === row.status) return;
    setSalvandoId(row.id);
    setMsgGlobal(null);
    try {
      await patchStatusSolicitacaoLgpd(row.id, { status: novo });
      setMsgGlobal("Status atualizado.");
      setPendentesPatch((prev) => {
        const next = { ...prev };
        delete next[row.id];
        return next;
      });
      await recarregar();
    } catch (e) {
      setErro(e instanceof Error ? e.message : "Falha ao atualizar status.");
    } finally {
      setSalvandoId(null);
    }
  };

  const executarAnon = async (diagId: string, solId: string) => {
    setExecId(solId);
    setMsgGlobal(null);
    setErro(null);
    try {
      const out = await postAnonimizarRespondenteLgpd(diagId, solId);
      setMsgGlobal(out.mensagem ?? "Anonimização concluída.");
      await recarregar();
    } catch (e) {
      setErro(e instanceof Error ? e.message : "Falha na anonimização.");
    } finally {
      setExecId(null);
    }
  };

  const exportarPortabilidade = async (
    diagnosticoId: string,
    solicitacaoId: string,
    formato: FormatoExportPortabilidade,
  ) => {
    const chave = `${solicitacaoId}-${formato}`;
    setExportandoChave(chave);
    setErro(null);
    setMsgGlobal(null);
    try {
      const blob = await fetchExportPortabilidadeDiagnostico({
        diagnosticoId,
        solicitacaoId,
        formato,
      });
      const nome =
        formato === "pacote_pdf"
          ? `qdi-portabilidade-${diagnosticoId}.pdf`
          : "qdi-diagnostico-export-v1.json";
      downloadBlob(blob, nome);
      setMsgGlobal(`Pacote ${formato === "pacote_pdf" ? "PDF" : "de dados"} baixado.`);
    } catch (e) {
      setErro(e instanceof Error ? e.message : "Falha no export.");
    } finally {
      setExportandoChave(null);
    }
  };

  return (
    <div className="container py-10 max-w-6xl">
      <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Privacidade LGPD</h1>
          <p className="text-muted-foreground mt-2 max-w-2xl">
            Registo centralizado de pedidos do titular (art. 18) por empresa e diagnóstico — sem repetir
            formulários na ficha técnica.
          </p>
        </div>
        <Button variant="outline" asChild>
          <Link href="/dashboard/diagnosticos">← Diagnósticos</Link>
        </Button>
      </div>

      {msgGlobal ? (
        <p className="mb-4 text-sm text-muted-foreground" role="status">
          {msgGlobal}
        </p>
      ) : null}
      {erro ? (
        <p className="mb-4 text-sm text-destructive" role="alert">
          {erro}
        </p>
      ) : null}

      <PrivacidadeNovaSolicitacaoCard
        diagnosticoIdInicial={diagnosticoIdInicial}
        onRegistrado={() => void recarregar()}
        onMensagem={(msg) => {
          setErro(null);
          setMsgGlobal(msg);
        }}
        onErro={setErro}
        onEmpresaSelecionada={(empresa) => {
          setEmpresaFiltro(empresa);
          if (empresa) setFiltrarSoEmpresa(true);
        }}
        onDiagnosticoUnicoSelecionado={setDiagUnicoRetif}
        onDiagnosticosEmpresaCarregados={(lista) =>
          setDiagIdsEmpresa(new Set(lista.map((d) => d.id)))
        }
      />

      {diagUnicoRetif ? (
        <RetificacaoDiagnosticoCard
          diagnosticoId={diagUnicoRetif.id}
          diagnosticoStatus={diagUnicoRetif.status}
          cardId="priv-retificacoes"
        />
      ) : (
        <Card className="mb-10 border-dashed" id="priv-retificacoes">
          <CardHeader>
            <CardTitle className="text-lg">Retificações (compliance)</CardTitle>
            <CardDescription>
              Marque <strong className="font-medium">apenas um</strong> diagnóstico na grelha acima para
              registrar retificação append-only (ADR-012).
            </CardDescription>
          </CardHeader>
        </Card>
      )}

      <Card className="mb-6" id="priv-lgpd-lista">
        <CardHeader className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <CardTitle className="text-lg">Solicitações registradas</CardTitle>
            <CardDescription>Filtre por status para acompanhar a operação LGPD.</CardDescription>
          </div>
          <div className="flex flex-wrap gap-2 items-center">
            {empresaFiltro ? (
              <label className="flex items-center gap-2 text-sm text-muted-foreground mr-2">
                <input
                  type="checkbox"
                  checked={filtrarSoEmpresa}
                  onChange={(e) => setFiltrarSoEmpresa(e.target.checked)}
                  className="rounded border-input"
                />
                Só {empresaFiltro.razao_social.slice(0, 24)}
                {empresaFiltro.razao_social.length > 24 ? "…" : ""}
              </label>
            ) : null}
            <Label htmlFor="filtro-st" className="sr-only">
              Filtrar por status
            </Label>
            <Select
              value={filtroStatus || "__todos__"}
              onValueChange={(v: string | null) =>
                setFiltroStatus(v == null || v === "__todos__" ? "" : v)
              }
            >
              <SelectTrigger id="filtro-st" className="w-[200px]">
                <SelectValue placeholder="Todos" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="__todos__">Todos os status</SelectItem>
                {STATUS_OPCOES.map((s) => (
                  <SelectItem key={s} value={s}>
                    {ROTULO_STATUS[s]}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button type="button" variant="secondary" size="sm" onClick={() => void recarregar()}>
              Atualizar
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {carregando ? (
            <p className="text-muted-foreground text-sm">Carregando…</p>
          ) : linhasFiltradas.length === 0 ? (
            <p className="text-muted-foreground text-sm">
              {filtrarSoEmpresa && empresaFiltro
                ? `Nenhuma solicitação para ${empresaFiltro.razao_social}.`
                : "Nenhuma solicitação encontrada."}
            </p>
          ) : (
            <div className="overflow-x-auto rounded-md border">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-muted/40 text-left">
                    <th className="p-3 font-medium">Tipo</th>
                    <th className="p-3 font-medium">Status</th>
                    <th className="p-3 font-medium">Empresa / diagnóstico</th>
                    <th className="p-3 font-medium">Titular</th>
                    <th className="p-3 font-medium">Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {linhasFiltradas.map((row) => {
                    const pendente = pendentesPatch[row.id] ?? row.status;
                    const podeExecutar =
                      row.tipo === "anonimizacao" &&
                      row.status === "deferida" &&
                      row.diagnostico_id != null;
                    const podeExportPort =
                      row.tipo === "portabilidade" &&
                      row.status === "deferida" &&
                      row.diagnostico_id != null;
                    return (
                      <tr key={row.id} className="border-b border-muted last:border-0 align-top">
                        <td className="p-3">
                          <Badge variant="outline">{ROTULO_TIPO[row.tipo] ?? row.tipo}</Badge>
                        </td>
                        <td className="p-3">
                          <div className="flex flex-col gap-2 min-w-[180px]">
                            <Select
                              value={pendente}
                              onValueChange={(v: string | null) =>
                                setPendentesPatch((prev) => ({
                                  ...prev,
                                  [row.id]: v ?? "",
                                }))
                              }
                            >
                              <SelectTrigger className="h-9">
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                {STATUS_OPCOES.map((s) => (
                                  <SelectItem key={s} value={s}>
                                    {ROTULO_STATUS[s]}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                            <Button
                              type="button"
                              size="sm"
                              variant="secondary"
                              disabled={salvandoId === row.id || pendente === row.status}
                              onClick={() => void aplicarStatus(row)}
                            >
                              {salvandoId === row.id ? "…" : "Gravar status"}
                            </Button>
                          </div>
                        </td>
                        <td className="p-3 font-mono text-xs break-all max-w-[14rem]">
                          {row.diagnostico_id ? (
                            <Link
                              href={hrefPrivacidadePainel({
                                diagnosticoId: String(row.diagnostico_id),
                                secao: "lgpd",
                              })}
                              className="text-primary underline"
                            >
                              {String(row.diagnostico_id).slice(0, 8)}…
                            </Link>
                          ) : (
                            "—"
                          )}
                          {empresaFiltro ? (
                            <span className="block text-[10px] text-muted-foreground font-sans mt-1">
                              {mascaraCnpj14(empresaFiltro.cnpj14)}
                            </span>
                          ) : null}
                        </td>
                        <td className="p-3 break-all">{row.solicitante_email}</td>
                        <td className="p-3">
                          <div className="flex flex-col gap-2 items-start">
                            {podeExportPort ? (
                              <div className="flex flex-wrap gap-1.5">
                                <Button
                                  type="button"
                                  size="sm"
                                  variant="secondary"
                                  disabled={exportandoChave !== null}
                                  onClick={() =>
                                    void exportarPortabilidade(
                                      row.diagnostico_id as string,
                                      row.id,
                                      "json",
                                    )
                                  }
                                >
                                  {exportandoChave === `${row.id}-json` ? "…" : "Dados"}
                                </Button>
                                <Button
                                  type="button"
                                  size="sm"
                                  variant="secondary"
                                  disabled={exportandoChave !== null}
                                  onClick={() =>
                                    void exportarPortabilidade(
                                      row.diagnostico_id as string,
                                      row.id,
                                      "pacote_pdf",
                                    )
                                  }
                                >
                                  {exportandoChave === `${row.id}-pacote_pdf` ? "…" : "PDF"}
                                </Button>
                              </div>
                            ) : null}
                            {podeExecutar ? (
                              <Button
                                type="button"
                                size="sm"
                                disabled={execId === row.id}
                                onClick={() =>
                                  void executarAnon(row.diagnostico_id as string, row.id)
                                }
                              >
                                {execId === row.id ? "…" : "Anonimizar"}
                              </Button>
                            ) : !podeExportPort ? (
                              <span className="text-muted-foreground text-xs">—</span>
                            ) : null}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      <p className="text-xs text-muted-foreground max-w-3xl">
        Base normativa: LGPD Lei 13.709/2018 (art. 18). Os registros preservam evidências do atendimento e apoiam a
        rastreabilidade das decisões.
      </p>
    </div>
  );
}
