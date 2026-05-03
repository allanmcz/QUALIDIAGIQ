"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { CheckCircle2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { getConclusaoSelfServiceVisualizacao } from "@/lib/api/self_service_diagnostico";
import { rotuloDimensao } from "@/lib/wizard/dimensao_labels";
import type { SelfServiceDiagnosticoResultado } from "@/lib/wizard/self_service_result";

/** Mesmas faixas do domínio (NivelMaturidade) — rótulo para leitura executiva. */
function rotuloNivelMaturidade(score: number | null | undefined): string | null {
  if (score === null || score === undefined || !Number.isFinite(score)) return null;
  if (score <= 20) return "Crítico";
  if (score <= 40) return "Inicial";
  if (score <= 60) return "Intermediário";
  if (score <= 80) return "Avançado";
  return "Exemplar";
}

function DiagnosticoConcluidoSelfServiceConteudo() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [dados, setDados] = useState<SelfServiceDiagnosticoResultado | null | undefined>(undefined);
  const [erro, setErro] = useState<string | null>(null);

  useEffect(() => {
    const id = searchParams.get("diagnostico_id")?.trim() ?? "";
    const token = searchParams.get("leitura_token")?.trim() ?? "";
    if (!id || !token) {
      setDados(null);
      setErro(null);
      return;
    }
    let cancelado = false;
    void (async () => {
      setErro(null);
      try {
        const r = await getConclusaoSelfServiceVisualizacao(id, token);
        if (!cancelado) setDados(r);
      } catch (e) {
        if (!cancelado) {
          setDados(null);
          setErro(e instanceof Error ? e.message : "Não foi possível carregar o diagnóstico.");
        }
      }
    })();
    return () => {
      cancelado = true;
    };
  }, [searchParams]);

  useEffect(() => {
    if (dados === null && erro === null) {
      router.replace("/");
    }
  }, [dados, erro, router]);

  if (dados === undefined) {
    return (
      <div className="container max-w-lg py-16 text-center text-sm text-muted-foreground">Carregando…</div>
    );
  }

  if (dados === null) {
    if (erro) {
      return (
        <div className="container max-w-lg py-16 space-y-4 text-center">
          <p className="text-sm text-destructive" role="alert">
            {erro}
          </p>
          <Button type="button" variant="outline" onClick={() => router.replace("/")}>
            Voltar ao início
          </Button>
        </div>
      );
    }
    return null;
  }

  const scoreValor =
    dados.score_geral !== null && dados.score_geral !== undefined && Number.isFinite(dados.score_geral)
      ? dados.score_geral
      : null;
  const scoreTexto = scoreValor !== null ? `${scoreValor.toFixed(1)} / 100` : "indisponível nesta resposta";
  const nivelTexto = rotuloNivelMaturidade(scoreValor);

  const linhasDimensao = dados.scores_por_dimensao ?? [];

  return (
    <div className="container max-w-2xl py-10 px-4 space-y-8">
      <div className="flex justify-center">
        <div className="flex h-16 w-16 items-center justify-center rounded-full bg-accent/15 text-accent">
          <CheckCircle2 className="h-8 w-8" aria-hidden />
        </div>
      </div>

      <div className="text-center space-y-2">
        <h1 className="text-2xl font-bold tracking-tight md:text-3xl">Diagnóstico concluído</h1>
        <p className="text-muted-foreground text-sm leading-relaxed max-w-md mx-auto">
          O questionário foi associado ao e-mail confirmado e armazenado no ambiente self-service. O painel
          completo (histórico, PDF, M12) continua ligado à sua conta na plataforma Tributiq, se desejar evoluir depois.
        </p>
      </div>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-lg">Resultado do diagnóstico</CardTitle>
          <CardDescription>
            Score geral e notas por dimensão (mesmo critério do relatório e do motor M03 — LC 214/2025 em contexto de
            maturidade organizacional). Dados obtidos do servidor (PostgreSQL).
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4 text-sm">
          <p>
            <span className="font-medium text-foreground">Empresa:</span> {dados.empresa_razao_social}
          </p>
          <div className="rounded-lg border bg-muted/30 px-4 py-3 space-y-1">
            <p className="text-base font-semibold text-foreground tabular-nums">Score geral: {scoreTexto}</p>
            {nivelTexto ? (
              <p className="text-sm text-muted-foreground">
                Nível de maturidade geral:{" "}
                <span className="font-medium text-foreground">{nivelTexto}</span>
              </p>
            ) : (
              <p className="text-xs text-muted-foreground leading-relaxed">
                Se o score não aparecer, confira a versão da API — o JSON deve incluir score agregado persistido.
              </p>
            )}
          </div>

          <div className="space-y-2">
            <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Por dimensão</p>
            {linhasDimensao.length > 0 ? (
              <div className="rounded-lg border border-border overflow-hidden">
                <table className="w-full text-sm caption-bottom">
                  <thead>
                    <tr className="border-b bg-muted/40 text-left text-xs text-muted-foreground">
                      <th className="px-3 py-2 font-medium">Dimensão</th>
                      <th className="px-3 py-2 font-medium text-right w-[5.5rem]">Nota</th>
                      <th className="px-3 py-2 font-medium text-right min-w-[7rem]">Nível</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border/80">
                    {linhasDimensao.map((linha) => {
                      const nv = rotuloNivelMaturidade(linha.valor);
                      return (
                        <tr key={linha.dimensao} className="bg-background">
                          <td className="px-3 py-2.5 align-top">
                            <span className="font-medium text-foreground leading-snug">
                              {rotuloDimensao(linha.dimensao)}
                            </span>
                            {linha.peso_total_aplicado != null && Number.isFinite(linha.peso_total_aplicado) ? (
                              <span className="mt-0.5 block text-[11px] text-muted-foreground tabular-nums">
                                Peso aplicado no diagnóstico: {linha.peso_total_aplicado.toFixed(1)}
                              </span>
                            ) : null}
                          </td>
                          <td className="px-3 py-2.5 text-right tabular-nums font-medium text-foreground align-top">
                            {linha.valor.toFixed(1)}
                          </td>
                          <td className="px-3 py-2.5 text-right text-muted-foreground align-top">
                            {nv ?? "—"}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="rounded-md border border-dashed px-3 py-2 text-xs text-muted-foreground leading-relaxed">
                O breakdown por dimensão não está disponível nesta resposta.
              </p>
            )}
          </div>

          <p className="text-muted-foreground text-xs leading-relaxed">
            Situação: <span className="font-medium text-foreground">{dados.status}</span>
            {" · "}
            ID: <span className="font-mono break-all">{dados.id}</span>
            {" · "}
            Relatório: {dados.locale_relatorio}
          </p>
        </CardContent>
        {/*
          Card raiz tem overflow-hidden: em sm:flex-row, dois filhos w-full estouram a largura
          e o segundo botão (login) era cortado. sm:flex-1 + min-w-0 reparte o espaço sem overflow.
        */}
        <CardFooter className="flex flex-col gap-2 sm:flex-row sm:items-stretch sm:gap-3">
          <Button asChild variant="outline" className="w-full min-w-0 bg-transparent sm:flex-1">
            <Link href="/">Voltar ao início</Link>
          </Button>
          <Button asChild className="w-full min-w-0 sm:flex-1">
            <Link href="/login?redirect=/wizard">Cadastrar ou entrar</Link>
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
}

export default function DiagnosticoConcluidoSelfServicePage() {
  return (
    <Suspense
      fallback={
        <div className="container max-w-lg py-16 text-center text-sm text-muted-foreground">Carregando…</div>
      }
    >
      <DiagnosticoConcluidoSelfServiceConteudo />
    </Suspense>
  );
}
