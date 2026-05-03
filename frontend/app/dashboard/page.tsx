"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchDiagnosticosResumo, type DiagnosticoResumoApi } from "@/lib/api/lista_diagnosticos";
import { getAccessToken } from "@/lib/api/config";
import { postVincularLeadsSelfService } from "@/lib/api/vincular_leads_self_service";

export default function DashboardPage() {
  const [itens, setItens] = useState<DiagnosticoResumoApi[] | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [msgVinculo, setMsgVinculo] = useState<string | null>(null);
  const [vinculando, setVinculando] = useState(false);

  useEffect(() => {
    let cancel = false;
    async function load() {
      if (!getAccessToken()) {
        setErro(null);
        setItens([]);
        return;
      }
      try {
        const rows = await fetchDiagnosticosResumo();
        if (!cancel) setItens(rows);
      } catch (e) {
        if (!cancel) setErro(e instanceof Error ? e.message : "Falha ao carregar diagnósticos.");
      }
    }
    load();
    return () => {
      cancel = true;
    };
  }, []);

  const recarregarLista = async () => {
    if (!getAccessToken()) return;
    try {
      const rows = await fetchDiagnosticosResumo();
      setItens(rows);
    } catch (e) {
      setErro(e instanceof Error ? e.message : "Falha ao carregar diagnósticos.");
    }
  };

  const semSessao = !getAccessToken();

  const importarLeadsSelfService = async () => {
    setMsgVinculo(null);
    setErro(null);
    setVinculando(true);
    try {
      const r = await postVincularLeadsSelfService();
      setMsgVinculo(
        r.total_vinculados === 0
          ? "Nenhum diagnóstico gratuito pendente (mesmo e-mail no fluxo OTP) para vincular."
          : `${r.total_vinculados} diagnóstico(s) do fluxo gratuito vinculado(s) a este painel.`,
      );
      await recarregarLista();
    } catch (e) {
      setErro(e instanceof Error ? e.message : "Falha ao vincular diagnósticos.");
    } finally {
      setVinculando(false);
    }
  };

  return (
    <div className="container py-10">
      <div className="flex flex-col gap-8">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Painel de Diagnósticos</h1>
            <p className="text-muted-foreground">
              Gerencie os diagnósticos e planos de ação das empresas vinculadas.
            </p>
          </div>
          <div className="flex flex-col items-stretch gap-2 sm:items-end shrink-0">
            {!semSessao && (
              <div className="flex flex-col gap-2 sm:flex-row sm:justify-end">
                <Button asChild variant="default">
                  <Link href="/wizard">Novo diagnóstico</Link>
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  disabled={vinculando}
                  onClick={() => void importarLeadsSelfService()}
                >
                  {vinculando ? "Importando…" : "Importar diagnósticos (OTP / gratuito)"}
                </Button>
              </div>
            )}
            {!semSessao && itens === null && (
              <p className="text-sm text-muted-foreground text-right" aria-live="polite">
                Carregando lista…
              </p>
            )}
          </div>
        </div>

        {semSessao && (
          <div className="rounded-lg border border-amber-500/40 bg-amber-500/10 p-4 text-sm">
            Para ver os diagnósticos do tenant faça{" "}
            <Button variant="link" className="p-0 h-auto align-baseline" asChild>
              <Link href="/login">login</Link>
            </Button>
            .
          </div>
        )}

        {!semSessao && erro && (
          <div className="rounded-lg border border-destructive/40 bg-destructive/10 p-4 text-sm text-destructive">
            {erro}
          </div>
        )}

        {!semSessao && msgVinculo && (
          <div className="rounded-lg border border-primary/30 bg-primary/5 p-4 text-sm text-foreground">
            {msgVinculo}
          </div>
        )}

        {!semSessao && !erro && itens !== null && itens.length === 0 && (
          <p className="text-muted-foreground text-sm">
            Nenhum diagnóstico encontrado para este tenant. Use o assistente em{" "}
            <Link href="/wizard" className="text-primary underline font-medium">
              /wizard
            </Link>
            . Se você já concluiu o assistente com o mesmo e-mail da conta B2B (fluxo OTP), use
            «Importar diagnósticos (OTP / gratuito)» acima para trazer esses registros para o painel.
          </p>
        )}

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {!semSessao &&
            itens?.map((diag) => {
              const score = diag.score_geral;
              const pct = score != null ? Math.min(100, Math.max(0, score)) : null;
              const quando = new Date(diag.finalizado_em ?? diag.criado_em).toLocaleDateString(
                "pt-BR",
                { day: "2-digit", month: "2-digit", year: "numeric" },
              );

              return (
                <Link key={diag.id} href={`/dashboard/diagnosticos/${diag.id}`}>
                  <Card className="hover:border-primary/50 transition-colors cursor-pointer h-full">
                    <CardHeader className="pb-2">
                      <div className="flex justify-between items-start gap-2">
                        <CardTitle className="text-lg leading-snug">{diag.empresa_razao_social}</CardTitle>
                        <Badge variant={diag.plano === "avancado" ? "default" : "secondary"}>
                          {diag.plano}
                        </Badge>
                      </div>
                      <CardDescription>
                        {diag.status === "finalizado" ? "Finalizado" : diag.status.replace("_", " ")} ·{" "}
                        {quando}
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="flex flex-col gap-1 mt-2">
                        <span className="text-sm font-medium text-muted-foreground">Score geral</span>
                        {pct != null ? (
                          <>
                            <span className="text-2xl font-bold">{pct.toFixed(1)}/100</span>
                            <div
                              className="h-2 rounded-full bg-muted overflow-hidden mt-3"
                              aria-hidden="true"
                            >
                              <div
                                className="h-full rounded-full transition-all"
                                style={{
                                  width: `${pct}%`,
                                  backgroundColor:
                                    pct >= 72 ? "rgb(22 163 74)" : pct >= 48 ? "rgb(234 179 8)" : "rgb(220 38 38)",
                                }}
                              />
                            </div>
                          </>
                        ) : (
                          <span className="text-muted-foreground text-sm">Aguardando finalização</span>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                </Link>
              );
            })}
        </div>
      </div>
    </div>
  );
}
