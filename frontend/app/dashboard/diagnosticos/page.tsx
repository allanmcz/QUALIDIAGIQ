"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchDiagnosticosResumo, type DiagnosticoResumoApi } from "@/lib/api/lista_diagnosticos";
import { temSessaoPainelParaApiCliente } from "@/lib/api/config";
import { postVincularLeadsSelfService } from "@/lib/api/vincular_leads_self_service";
import { buildEmpresaDiagnosticosHref } from "@/lib/dashboard/empresa_diagnostico_urls";

/** Lista do tenant + atalhos (novo diagnóstico, importar OTP) — rota canónica após login. */
export default function PainelDiagnosticosPage() {
  const [itens, setItens] = useState<DiagnosticoResumoApi[] | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [msgVinculo, setMsgVinculo] = useState<string | null>(null);
  const [vinculando, setVinculando] = useState(false);

  useEffect(() => {
    let cancel = false;
    async function load() {
      if (!temSessaoPainelParaApiCliente()) {
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
    if (!temSessaoPainelParaApiCliente()) return;
    try {
      const rows = await fetchDiagnosticosResumo();
      setItens(rows);
    } catch (e) {
      setErro(e instanceof Error ? e.message : "Falha ao carregar diagnósticos.");
    }
  };

  const semSessao = !temSessaoPainelParaApiCliente();

  const importarLeadsSelfService = async () => {
    setMsgVinculo(null);
    setErro(null);
    setVinculando(true);
    try {
      const r = await postVincularLeadsSelfService();
      setMsgVinculo(
        r.total_vinculados === 0
          ? "Nenhum registro elegível: só existem diagnósticos no «pool» self-service (após OTP), plano gratuito, com e-mail do respondente igual ao do seu login na plataforma. Diagnósticos feitos já com sessão iniciada no painel não entram aqui — já estão no seu tenant."
          : `${r.total_vinculados} diagnóstico(s) do fluxo gratuito (OTP / self-service) foram trazidos para este painel.`,
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
            <h1 className="text-3xl font-bold tracking-tight">Painel de diagnósticos</h1>
            <p className="text-muted-foreground">
              Gerencie os diagnósticos e planos de ação das empresas vinculadas.
            </p>
          </div>
          <div className="flex flex-col items-stretch gap-2 sm:items-end shrink-0">
            {!semSessao && (
              <div className="flex w-full max-w-xl flex-col gap-3 sm:max-w-none sm:items-end">
                <div className="flex flex-col gap-2 sm:flex-row sm:justify-end">
                  <Button asChild variant="default">
                    <Link href="/wizard">Novo diagnóstico</Link>
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    disabled={vinculando}
                    onClick={() => void importarLeadsSelfService()}
                    aria-describedby="ajuda-importar-otp"
                  >
                    {vinculando ? "Importando…" : "Importar do fluxo OTP (gratuito)"}
                  </Button>
                  <Button asChild variant="outline">
                    <Link href="/dashboard/privacidade">Privacidade LGPD</Link>
                  </Button>
                </div>
                <p
                  id="ajuda-importar-otp"
                  className="text-xs text-muted-foreground text-left sm:text-right leading-relaxed max-w-md sm:ml-auto"
                >
                  Use apenas se você concluiu o assistente <strong className="font-medium text-foreground">sem</strong>{" "}
                  conta na plataforma: código no e-mail → gravação no ambiente self-service. A API só traz linhas em que o
                  e-mail do respondente é o <strong className="font-medium text-foreground">mesmo</strong> do seu
                  login atual e o plano é gratuito. Se você já estava com sessão iniciada e usou «Novo diagnóstico», os
                  itens já aparecem na lista abaixo — não precisam de importação.
                </p>
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
          <div
            className="rounded-lg border border-destructive/40 bg-destructive/10 p-4 text-sm text-destructive"
            role="alert"
            aria-live="assertive"
          >
            {erro}
          </div>
        )}

        {!semSessao && msgVinculo && (
          <div
            className="rounded-lg border border-primary/30 bg-primary/5 p-4 text-sm text-foreground"
            role="status"
            aria-live="polite"
          >
            {msgVinculo}
          </div>
        )}

        {!semSessao && !erro && itens !== null && itens.length === 0 && (
          <p
            className="text-muted-foreground text-sm leading-relaxed max-w-2xl"
            role="status"
            aria-live="polite"
          >
            Nenhum diagnóstico neste painel ainda. Use <strong className="text-foreground">Novo diagnóstico</strong>{" "}
            acima ou inicie em{" "}
            <Link href="/wizard" className="text-primary underline font-medium">
              /wizard
            </Link>{" "}
            (logado). Se você só usou o fluxo com código por e-mail (lead), clique em «Importar do fluxo OTP
            (gratuito)» — desde que o e-mail confirmado no OTP seja o mesmo do login na plataforma.
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

              const detailHref = `/dashboard/diagnosticos/${diag.id}`;
              const cnpj14 =
                diag.empresa_cnpj && diag.empresa_cnpj.replace(/\D/g, "").length === 14
                  ? diag.empresa_cnpj.replace(/\D/g, "")
                  : null;

              return (
                <Card
                  key={diag.id}
                  className="h-full flex flex-col border-border/80 hover:border-primary/40 transition-colors shadow-sm"
                >
                  <CardHeader className="pb-2 space-y-2">
                    <div className="flex justify-between items-start gap-2">
                      <Link href={detailHref} className="min-w-0 group">
                        <CardTitle className="text-lg leading-snug group-hover:text-primary transition-colors">
                          {diag.empresa_razao_social}
                        </CardTitle>
                      </Link>
                      <Badge variant={diag.plano === "avancado" ? "default" : "secondary"}>{diag.plano}</Badge>
                    </div>
                    <p className="text-xs text-muted-foreground tabular-nums">
                      {cnpj14
                        ? `CNPJ ${cnpj14.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/, "$1.$2.$3/$4-$5")}`
                        : "CNPJ não informado"}
                    </p>
                    {cnpj14 ? (
                      <Link
                        href={buildEmpresaDiagnosticosHref(cnpj14, diag.empresa_razao_social)}
                        className="text-xs font-medium text-primary hover:underline inline-block w-fit"
                      >
                        Ver grelha por empresa (todos os ciclos)
                      </Link>
                    ) : null}
                    <CardDescription>
                      <Link href={detailHref} className="hover:underline">
                        {diag.status === "finalizado" ? "Finalizado" : diag.status.replace("_", " ")} · {quando}
                      </Link>
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="flex-1">
                    <Link href={detailHref} className="block">
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
                    </Link>
                  </CardContent>
                </Card>
              );
            })}
        </div>
      </div>
    </div>
  );
}
