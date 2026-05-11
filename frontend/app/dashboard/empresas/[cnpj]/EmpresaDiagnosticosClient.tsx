"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchDiagnosticosResumo, type DiagnosticoResumoApi } from "@/lib/api/lista_diagnosticos";
import { getAccessToken } from "@/lib/api/config";
import { buildWizardUrlNovaDiagnosticoEmpresa } from "@/lib/dashboard/empresa_diagnostico_urls";

function mascaraCnpj14(d: string): string {
  const c = d.replace(/\D/g, "");
  if (c.length !== 14) return d;
  return c.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/, "$1.$2.$3/$4-$5");
}

export default function EmpresaDiagnosticosClient({
  cnpjNormalizado,
  razaoSocialHint,
}: {
  cnpjNormalizado: string;
  razaoSocialHint: string;
}) {
  const [diagnosticos, setDiagnosticos] = useState<DiagnosticoResumoApi[] | null>(null);
  const [erro, setErro] = useState<string | null>(null);

  useEffect(() => {
    let cancel = false;
    async function load() {
      if (!getAccessToken()) {
        setDiagnosticos([]);
        return;
      }
      try {
        const rows = await fetchDiagnosticosResumo(200, 0, {
          empresaCnpj14: cnpjNormalizado,
        });
        if (!cancel) setDiagnosticos(rows);
      } catch (e) {
        if (!cancel) setErro(e instanceof Error ? e.message : "Falha ao carregar diagnósticos.");
      }
    }
    void load();
    return () => {
      cancel = true;
    };
  }, [cnpjNormalizado]);

  const tituloEmpresa = useMemo(() => {
    const hint = razaoSocialHint.trim();
    if (hint.length >= 3) return hint;
    const primeiro = diagnosticos?.[0]?.empresa_razao_social?.trim();
    if (primeiro && primeiro.length >= 3) return primeiro;
    return `Empresa · CNPJ ${mascaraCnpj14(cnpjNormalizado)}`;
  }, [razaoSocialHint, diagnosticos, cnpjNormalizado]);

  const daEmpresa = diagnosticos ?? [];

  const semSessao = !getAccessToken();

  return (
    <div className="container py-10">
      <div className="flex flex-col gap-6">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div className="space-y-1">
            <Link
              href="/dashboard/diagnosticos"
              className="text-sm text-primary hover:underline inline-block"
            >
              ← Voltar ao painel de diagnósticos
            </Link>
            <h1 className="text-2xl md:text-3xl font-bold tracking-tight">{tituloEmpresa}</h1>
            <p className="text-muted-foreground text-sm tabular-nums">
              CNPJ {mascaraCnpj14(cnpjNormalizado)} · {daEmpresa.length} diagnóstico(s) neste tenant
            </p>
          </div>
          {!semSessao && (
            <Button asChild className="shrink-0 w-full sm:w-auto">
              <Link href={buildWizardUrlNovaDiagnosticoEmpresa(cnpjNormalizado, tituloEmpresa)}>
                Novo diagnóstico (esta empresa)
              </Link>
            </Button>
          )}
        </div>

        {semSessao && (
          <div className="rounded-lg border border-amber-500/40 bg-amber-500/10 p-4 text-sm">
            Para ver e criar diagnósticos faça{" "}
            <Link href="/login" className="text-primary font-medium underline">
              login
            </Link>
            .
          </div>
        )}

        {erro && (
          <div
            className="rounded-lg border border-destructive/40 bg-destructive/10 p-4 text-sm text-destructive"
            role="alert"
          >
            {erro}
          </div>
        )}

        {!semSessao && !erro && diagnosticos !== null && daEmpresa.length === 0 && (
          <p className="text-muted-foreground text-sm max-w-2xl leading-relaxed">
            Nenhum diagnóstico encontrado para este CNPJ neste tenant (ou os registos ainda não incluem{" "}
            <span className="font-mono tabular-nums">{cnpjNormalizado}</span>). Pode iniciar um novo ciclo com o botão
            acima.
          </p>
        )}

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {!semSessao &&
            daEmpresa.map((diag) => {
              const score = diag.score_geral;
              const pct = score != null ? Math.min(100, Math.max(0, score)) : null;
              const quando = new Date(diag.finalizado_em ?? diag.criado_em).toLocaleDateString(
                "pt-BR",
                { day: "2-digit", month: "2-digit", year: "numeric" },
              );
              const detailHref = `/dashboard/diagnosticos/${diag.id}`;

              return (
                <Card key={diag.id} className="h-full flex flex-col border-primary/15 shadow-sm">
                  <CardHeader className="pb-2 space-y-2">
                    <div className="flex justify-between items-start gap-2">
                      <Link href={detailHref} className="min-w-0 group">
                        <CardTitle className="text-lg leading-snug group-hover:text-primary transition-colors">
                          {diag.empresa_razao_social}
                        </CardTitle>
                      </Link>
                      <Badge variant={diag.plano === "avancado" ? "default" : "secondary"}>
                        {diag.plano}
                      </Badge>
                    </div>
                    <CardDescription>
                      <Link href={detailHref} className="hover:underline">
                        {diag.status === "finalizado" ? "Finalizado" : diag.status.replace("_", " ")} · {quando}
                      </Link>
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="flex-1 pt-0">
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
