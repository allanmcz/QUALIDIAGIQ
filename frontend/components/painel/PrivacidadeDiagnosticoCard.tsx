"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { downloadBlob } from "@/lib/browser_download";
import {
  fetchExportPortabilidadeDiagnostico,
  fetchSolicitacoesLgpd,
  postAnonimizarRespondenteLgpd,
  type FormatoExportPortabilidade,
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

type Props = {
  diagnosticoId: string;
  diagnosticoStatus: string;
};

/**
 * Solicitações LGPD ligadas a este diagnóstico + atalho para executar anonimização após deferimento.
 */
export function PrivacidadeDiagnosticoCard({ diagnosticoId, diagnosticoStatus }: Props) {
  const [linhas, setLinhas] = useState<SolicitacaoTitularLgpd[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);
  const [mensagem, setMensagem] = useState<string | null>(null);
  const [executandoId, setExecutandoId] = useState<string | null>(null);
  /** `${solicitacaoId}-${formato}` enquanto descarrega export portabilidade */
  const [exportandoChave, setExportandoChave] = useState<string | null>(null);

  const filtradas = useMemo(
    () =>
      linhas.filter(
        (s) => s.diagnostico_id != null && String(s.diagnostico_id) === String(diagnosticoId),
      ),
    [linhas, diagnosticoId],
  );

  const recarregar = useCallback(async () => {
    setCarregando(true);
    setErro(null);
    try {
      const todas = await fetchSolicitacoesLgpd({ limit: 200 });
      setLinhas(todas);
    } catch (e) {
      setErro(e instanceof Error ? e.message : "Falha ao carregar solicitações LGPD.");
      setLinhas([]);
    } finally {
      setCarregando(false);
    }
  }, []);

  useEffect(() => {
    void recarregar();
  }, [recarregar]);

  const podeExecutarAnonimizacao =
    diagnosticoStatus === "finalizado";

  const exportarPortabilidade = async (solicitacaoId: string, formato: FormatoExportPortabilidade) => {
    const chave = `${solicitacaoId}-${formato}`;
    setExportandoChave(chave);
    setErro(null);
    setMensagem(null);
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
      setMensagem(`Pacote ${formato === "pacote_pdf" ? "PDF" : "JSON"} descarregado.`);
    } catch (e) {
      setErro(e instanceof Error ? e.message : "Falha no export de portabilidade.");
    } finally {
      setExportandoChave(null);
    }
  };

  const executarAnonimizacao = async (solicitacaoId: string) => {
    setExecutandoId(solicitacaoId);
    setMensagem(null);
    setErro(null);
    try {
      const out = await postAnonimizarRespondenteLgpd(diagnosticoId, solicitacaoId);
      setMensagem(out.mensagem ?? "Anonimização aplicada; solicitação concluída.");
      await recarregar();
    } catch (e) {
      setErro(e instanceof Error ? e.message : "Falha na anonimização.");
    } finally {
      setExecutandoId(null);
    }
  };

  if (carregando && filtradas.length === 0 && !erro) {
    return (
      <Card id="diag-privacidade-lgpd" className="mb-10 scroll-mt-24">
        <CardHeader>
          <CardTitle className="text-lg">Privacidade LGPD (este diagnóstico)</CardTitle>
          <CardDescription>A carregar solicitações…</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  if (filtradas.length === 0 && !erro) {
    return (
      <Card id="diag-privacidade-lgpd" className="mb-10 scroll-mt-24">
        <CardHeader>
          <CardTitle className="text-lg">Privacidade LGPD (este diagnóstico)</CardTitle>
          <CardDescription>
            Nenhuma solicitação do titular ligada a este diagnóstico. Use o painel{" "}
            <Link href="/dashboard/privacidade" className="text-primary underline">
              Privacidade LGPD
            </Link>{" "}
            para registar ou filtrar pedidos (art. 18).
          </CardDescription>
        </CardHeader>
      </Card>
    );
  }

  return (
    <Card id="diag-privacidade-lgpd" className="mb-10 scroll-mt-24">
      <CardHeader>
        <CardTitle className="text-lg">Privacidade LGPD (este diagnóstico)</CardTitle>
        <CardDescription>
          Pedidos do titular vinculados a este ID.{" "}
          <strong className="font-medium text-foreground">Portabilidade deferida</strong>: descarregar JSON ou PDF com
          anexo JSON (LGPD art. 18, V).{" "}
          <strong className="font-medium text-foreground">Anonimização deferida</strong>: executar troca técnica do
          respondente (trilha WORM + <code className="text-xs">lgpd_anonimizacao_log</code>).
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {erro ? <p className="text-sm text-destructive">{erro}</p> : null}
        {mensagem ? (
          <p className="text-sm text-muted-foreground" role="status">
            {mensagem}
          </p>
        ) : null}
        <ul className="space-y-3 list-none p-0 m-0">
          {filtradas.map((s) => {
            const podeBotao =
              s.tipo === "anonimizacao" &&
              s.status === "deferida" &&
              podeExecutarAnonimizacao;
            const podeExportPort =
              s.tipo === "portabilidade" && s.status === "deferida" && podeExecutarAnonimizacao;
            return (
              <li
                key={s.id}
                className="rounded-lg border bg-muted/20 px-4 py-3 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"
              >
                <div className="space-y-1 min-w-0">
                  <div className="flex flex-wrap gap-2 items-center">
                    <Badge variant="outline">{ROTULO_TIPO[s.tipo] ?? s.tipo}</Badge>
                    <Badge variant="secondary">{ROTULO_STATUS[s.status] ?? s.status}</Badge>
                  </div>
                  <p className="text-sm text-muted-foreground truncate" title={s.solicitante_email}>
                    Titular: {s.solicitante_email}
                  </p>
                  <p className="text-xs text-muted-foreground font-mono break-all">ID: {s.id}</p>
                </div>
                <div className="flex flex-wrap gap-2 shrink-0">
                  {podeExportPort ? (
                    <>
                      <Button
                        type="button"
                        size="sm"
                        variant="secondary"
                        disabled={exportandoChave !== null}
                        onClick={() => void exportarPortabilidade(s.id, "json")}
                      >
                        {exportandoChave === `${s.id}-json` ? "JSON…" : "Export JSON"}
                      </Button>
                      <Button
                        type="button"
                        size="sm"
                        variant="secondary"
                        disabled={exportandoChave !== null}
                        onClick={() => void exportarPortabilidade(s.id, "pacote_pdf")}
                      >
                        {exportandoChave === `${s.id}-pacote_pdf` ? "PDF…" : "Export PDF"}
                      </Button>
                    </>
                  ) : s.tipo === "portabilidade" && s.status === "deferida" && !podeExecutarAnonimizacao ? (
                    <p className="text-xs text-amber-700 max-w-xs">
                      Export de portabilidade só com diagnóstico finalizado e hash de evidência.
                    </p>
                  ) : null}
                  {podeBotao ? (
                    <Button
                      type="button"
                      size="sm"
                      variant="default"
                      disabled={executandoId === s.id}
                      onClick={() => void executarAnonimizacao(s.id)}
                    >
                      {executandoId === s.id ? "A executar…" : "Executar anonimização do respondente"}
                    </Button>
                  ) : s.tipo === "anonimizacao" && s.status === "deferida" && !podeExecutarAnonimizacao ? (
                    <p className="text-xs text-amber-700 max-w-xs">
                      Anonimização só após o diagnóstico estar finalizado (evidência WORM).
                    </p>
                  ) : null}
                  <Button type="button" size="sm" variant="outline" asChild>
                    <Link href="/dashboard/privacidade">Painel LGPD</Link>
                  </Button>
                </div>
              </li>
            );
          })}
        </ul>
      </CardContent>
    </Card>
  );
}
