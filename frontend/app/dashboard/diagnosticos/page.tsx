"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { fetchDiagnosticosResumo, type DiagnosticoResumoApi } from "@/lib/api/lista_diagnosticos";
import { temSessaoPainelParaApiCliente } from "@/lib/api/config";
import { postVincularLeadsSelfService } from "@/lib/api/vincular_leads_self_service";
import { ArquivarEmpresaPainelButton } from "@/components/painel/ArquivarEmpresaPainelButton";
import { fetchCnpjsArquivadosPainel } from "@/lib/api/arquivar_empresa_painel";
import { buildEmpresaDiagnosticosHref } from "@/lib/dashboard/empresa_diagnostico_urls";
import { buildWizardUrlNovaEmpresa } from "@/lib/wizard/wizard_modo_empresa";

/** Lista do tenant + atalhos (novo diagnóstico, importar OTP) — rota canónica após login. */
export default function PainelDiagnosticosPage() {
  const ajudaImportarOtp =
    "Use apenas se você concluiu o assistente sem conta na plataforma e confirmou o resultado por código no e-mail. A importação procura diagnósticos gratuitos vinculados ao mesmo e-mail do seu login atual. Se você já estava com sessão iniciada e usou «Nova empresa», os itens já aparecem na lista abaixo — não precisam de importação.";
  const [itens, setItens] = useState<DiagnosticoResumoApi[] | null>(null);
  const [carregandoLista, setCarregandoLista] = useState(true);
  const [erro, setErro] = useState<string | null>(null);
  const [msgVinculo, setMsgVinculo] = useState<string | null>(null);
  const [msgArquivo, setMsgArquivo] = useState<string | null>(null);
  const [verArquivadas, setVerArquivadas] = useState(false);
  const [cnpjsArquivados, setCnpjsArquivados] = useState<Set<string>>(new Set());
  const [vinculando, setVinculando] = useState(false);

  const recarregarCnpjsArquivados = async () => {
    if (!temSessaoPainelParaApiCliente()) return;
    try {
      const lista = await fetchCnpjsArquivadosPainel();
      setCnpjsArquivados(new Set(lista));
    } catch {
      setCnpjsArquivados(new Set());
    }
  };

  useEffect(() => {
    let cancel = false;
    async function load() {
      if (!temSessaoPainelParaApiCliente()) {
        setErro(null);
        setItens([]);
        setCarregandoLista(false);
        return;
      }
      setCarregandoLista(true);
      setErro(null);
      try {
        const rows = await fetchDiagnosticosResumo(100, 0, {
          incluirArquivadas: verArquivadas,
        });
        if (!cancel) setItens(rows);
        if (verArquivadas && !cancel) {
          const lista = await fetchCnpjsArquivadosPainel();
          if (!cancel) setCnpjsArquivados(new Set(lista));
        }
      } catch (e) {
        if (!cancel) setErro(e instanceof Error ? e.message : "Falha ao carregar diagnósticos.");
      } finally {
        if (!cancel) setCarregandoLista(false);
      }
    }
    void load();
    return () => {
      cancel = true;
    };
  }, [verArquivadas]);

  const recarregarLista = async () => {
    if (!temSessaoPainelParaApiCliente()) return;
    try {
      const rows = await fetchDiagnosticosResumo(100, 0, {
        incluirArquivadas: verArquivadas,
      });
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
          ? "Nenhum diagnóstico elegível para importar. Apenas resultados gratuitos confirmados por e-mail, com o mesmo e-mail do seu login atual, podem ser trazidos para este painel."
          : `${r.total_vinculados} diagnóstico(s) gratuito(s) confirmado(s) por e-mail foram trazidos para este painel.`,
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
                    <Link href={buildWizardUrlNovaEmpresa()}>Nova empresa</Link>
                  </Button>
                  <TooltipProvider delayDuration={250}>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <span className="inline-flex">
                          <Button
                            type="button"
                            variant="outline"
                            disabled={vinculando}
                            onClick={() => void importarLeadsSelfService()}
                            aria-describedby="ajuda-importar-otp"
                          >
                            {vinculando ? "Importando…" : "Importar Fluxo OTP"}
                          </Button>
                        </span>
                      </TooltipTrigger>
                      <TooltipContent
                        id="ajuda-importar-otp"
                        side="bottom"
                        align="end"
                        className="max-w-md text-left leading-relaxed"
                      >
                        {ajudaImportarOtp}
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                  <Button asChild variant="outline">
                    <Link href="/dashboard/privacidade">Privacidade LGPD</Link>
                  </Button>
                </div>
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
            Para ver seus diagnósticos e planos de ação, faça{" "}
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

        {!semSessao && msgArquivo && (
          <div
            className="rounded-lg border border-primary/30 bg-primary/5 p-4 text-sm text-foreground"
            role="status"
            aria-live="polite"
          >
            {msgArquivo}
          </div>
        )}

        {!semSessao && (
          <div className="flex flex-wrap items-center gap-2">
            <Button
              type="button"
              variant={verArquivadas ? "secondary" : "outline"}
              size="sm"
              onClick={() => {
                setVerArquivadas((v) => {
                  const next = !v;
                  if (next) void recarregarCnpjsArquivados();
                  return next;
                });
                setMsgArquivo(null);
              }}
            >
              {verArquivadas ? "Ocultar empresas arquivadas" : "Ver empresas arquivadas"}
            </Button>
          </div>
        )}

        {!semSessao && carregandoLista && itens === null && (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3" aria-busy="true" aria-label="Carregando diagnósticos">
            {[1, 2, 3].map((k) => (
              <div key={k} className="h-48 animate-pulse rounded-lg bg-muted" />
            ))}
          </div>
        )}

        {!semSessao && !erro && !carregandoLista && itens !== null && itens.length === 0 && (
          <p
            className="text-muted-foreground text-sm leading-relaxed max-w-2xl"
            role="status"
            aria-live="polite"
          >
            Nenhum diagnóstico neste painel ainda. Use{" "}
            <strong className="text-foreground">Nova empresa</strong>{" "}
            acima ou inicie em{" "}
            <Link href="/wizard" className="text-primary underline font-medium">
              /wizard
            </Link>{" "}
            com acesso ao painel. Se você concluiu pelo código enviado por e-mail, clique em «Importar Fluxo OTP» —
            desde que o e-mail confirmado no OTP seja o mesmo do login na plataforma.
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

              const cnpj14 =
                diag.empresa_cnpj && diag.empresa_cnpj.replace(/\D/g, "").length === 14
                  ? diag.empresa_cnpj.replace(/\D/g, "")
                  : null;
              const empresaHref = cnpj14
                ? buildEmpresaDiagnosticosHref(cnpj14, diag.empresa_razao_social, {
                    expandDiagnosticoId: diag.id,
                  })
                : `/dashboard/diagnosticos/${diag.id}`;

              return (
                <Card
                  key={diag.id}
                  className="h-full flex flex-col border-border/80 hover:border-primary/40 transition-colors shadow-sm"
                >
                  <CardHeader className="pb-2 space-y-2">
                    <div className="flex justify-between items-start gap-2">
                      <Link href={empresaHref} className="min-w-0 group">
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
                        href={empresaHref}
                        className="text-xs font-medium text-primary hover:underline inline-block w-fit"
                      >
                        Ver todos os diagnósticos da empresa
                      </Link>
                    ) : null}
                    <CardDescription>
                      <Link href={empresaHref} className="hover:underline">
                        {diag.status === "finalizado" ? "Finalizado" : diag.status.replace("_", " ")} · {quando}
                      </Link>
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="flex-1">
                    <Link href={empresaHref} className="block">
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
                    {cnpj14 ? (
                      <div className="mt-4 pt-3 border-t border-border/60">
                        <ArquivarEmpresaPainelButton
                          cnpj14={cnpj14}
                          razaoSocial={diag.empresa_razao_social}
                          arquivada={cnpjsArquivados.has(cnpj14)}
                          variant="outline"
                          className="w-full"
                          onConcluido={(mensagem) => {
                            setMsgVinculo(null);
                            setMsgArquivo(mensagem);
                            setErro(null);
                            void recarregarCnpjsArquivados();
                            void recarregarLista();
                          }}
                        />
                      </div>
                    ) : null}
                  </CardContent>
                </Card>
              );
            })}
        </div>
      </div>
    </div>
  );
}
