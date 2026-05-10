"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  fetchSolicitacoesLgpd,
  patchStatusSolicitacaoLgpd,
  postAnonimizarRespondenteLgpd,
  postRegistrarSolicitacaoLgpd,
  type SolicitacaoTitularLgpd,
} from "@/lib/api/privacidade_lgpd";

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

export default function DashboardPrivacidadePage() {
  const [linhas, setLinhas] = useState<SolicitacaoTitularLgpd[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);
  const [filtroStatus, setFiltroStatus] = useState<string>("");
  const [pendentesPatch, setPendentesPatch] = useState<Record<string, string>>({});
  const [salvandoId, setSalvandoId] = useState<string | null>(null);
  const [execId, setExecId] = useState<string | null>(null);
  const [msgGlobal, setMsgGlobal] = useState<string | null>(null);

  const [regTipo, setRegTipo] = useState("anonimizacao");
  const [regEmail, setRegEmail] = useState("");
  const [regDiag, setRegDiag] = useState("");
  const [regSalvando, setRegSalvando] = useState(false);

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

  const registrarDemo = async () => {
    const email = regEmail.trim();
    if (!email) {
      setErro("Informe o e-mail do solicitante.");
      return;
    }
    const diag = regDiag.trim();
    setRegSalvando(true);
    setErro(null);
    setMsgGlobal(null);
    try {
      await postRegistrarSolicitacaoLgpd({
        tipo: regTipo,
        solicitante_email: email,
        diagnostico_id: diag.length >= 32 ? diag : undefined,
        payload: { origem: "painel_demo" },
      });
      setMsgGlobal("Solicitação registada.");
      setRegEmail("");
      setRegDiag("");
      await recarregar();
    } catch (e) {
      setErro(e instanceof Error ? e.message : "Falha ao registar.");
    } finally {
      setRegSalvando(false);
    }
  };

  return (
    <div className="container py-10 max-w-6xl">
      <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Privacidade LGPD</h1>
          <p className="text-muted-foreground mt-2 max-w-2xl">
            Solicitações do titular (art. 18) no seu tenant. Para demonstração: registe um pedido,
            altere o status para <strong className="font-medium text-foreground">deferida</strong>
            {", "}
            e execute a anonimização do respondente quando o diagnóstico estiver{" "}
            <strong className="font-medium text-foreground">finalizado</strong>.
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

      <Card className="mb-10">
        <CardHeader>
          <CardTitle className="text-lg">Registar solicitação (demonstração)</CardTitle>
          <CardDescription>
            Simula entrada pelo canal da plataforma. UUID do diagnóstico opcional — copie da página de
            detalhe do diagnóstico.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="space-y-2">
            <Label htmlFor="lgpd-tipo">Tipo</Label>
            <Select
              value={regTipo}
              onValueChange={(v: string | null) => setRegTipo(v ?? "")}
            >
              <SelectTrigger id="lgpd-tipo">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {Object.entries(ROTULO_TIPO).map(([k, v]) => (
                  <SelectItem key={k} value={k}>
                    {v}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2 sm:col-span-2">
            <Label htmlFor="lgpd-email">E-mail do solicitante</Label>
            <Input
              id="lgpd-email"
              type="email"
              autoComplete="email"
              placeholder="titular@empresa.com"
              value={regEmail}
              onChange={(e) => setRegEmail(e.target.value)}
            />
          </div>
          <div className="space-y-2 sm:col-span-2 lg:col-span-2">
            <Label htmlFor="lgpd-diag">ID do diagnóstico (opcional)</Label>
            <Input
              id="lgpd-diag"
              placeholder="UUID — ver painel do diagnóstico"
              value={regDiag}
              onChange={(e) => setRegDiag(e.target.value)}
              className="font-mono text-sm"
            />
          </div>
          <div className="flex items-end">
            <Button type="button" disabled={regSalvando} onClick={() => void registrarDemo()}>
              {regSalvando ? "A registar…" : "Registar"}
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card className="mb-6">
        <CardHeader className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <CardTitle className="text-lg">Lista de solicitações</CardTitle>
            <CardDescription>Filtro opcional por status no servidor.</CardDescription>
          </div>
          <div className="flex flex-wrap gap-2 items-center">
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
            <p className="text-muted-foreground text-sm">A carregar…</p>
          ) : linhas.length === 0 ? (
            <p className="text-muted-foreground text-sm">Nenhuma solicitação encontrada.</p>
          ) : (
            <div className="overflow-x-auto rounded-md border">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-muted/40 text-left">
                    <th className="p-3 font-medium">Tipo</th>
                    <th className="p-3 font-medium">Status</th>
                    <th className="p-3 font-medium">Diagnóstico</th>
                    <th className="p-3 font-medium">Titular</th>
                    <th className="p-3 font-medium">Acções</th>
                  </tr>
                </thead>
                <tbody>
                  {linhas.map((row) => {
                    const pendente = pendentesPatch[row.id] ?? row.status;
                    const podeExecutar =
                      row.tipo === "anonimizacao" &&
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
                              href={`/dashboard/diagnosticos/${row.diagnostico_id}`}
                              className="text-primary underline"
                            >
                              {row.diagnostico_id}
                            </Link>
                          ) : (
                            "—"
                          )}
                        </td>
                        <td className="p-3 break-all">{row.solicitante_email}</td>
                        <td className="p-3">
                          {podeExecutar ? (
                            <Button
                              type="button"
                              size="sm"
                              disabled={execId === row.id}
                              onClick={() =>
                                void executarAnon(row.diagnostico_id as string, row.id)
                              }
                            >
                              {execId === row.id ? "…" : "Executar anonimização"}
                            </Button>
                          ) : (
                            <span className="text-muted-foreground text-xs">
                              {row.tipo === "anonimizacao" && row.status === "deferida"
                                ? "Defina diagnóstico"
                                : "—"}
                            </span>
                          )}
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
        Base normativa: LGPD Lei 13.709/2018 (art. 18). Execução técnica alinhada ao WORM do diagnóstico
        finalizado (LC 214/2025 / evidências — ver migrations 0025 e 0029).
      </p>
    </div>
  );
}
