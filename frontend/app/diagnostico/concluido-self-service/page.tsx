"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
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
import {
  loadSelfServiceDiagnosticoResultado,
  type SelfServiceDiagnosticoResultado,
} from "@/lib/wizard/self_service_result";

/** Mesmas faixas do domínio (NivelMaturidade) — rótulo para leitura executiva. */
function rotuloNivelMaturidade(score: number | null | undefined): string | null {
  if (score === null || score === undefined || !Number.isFinite(score)) return null;
  if (score <= 20) return "Crítico";
  if (score <= 40) return "Inicial";
  if (score <= 60) return "Intermediário";
  if (score <= 80) return "Avançado";
  return "Exemplar";
}

export default function DiagnosticoConcluidoSelfServicePage() {
  const router = useRouter();
  const [dados, setDados] = useState<SelfServiceDiagnosticoResultado | null | undefined>(undefined);

  useEffect(() => {
    const r = loadSelfServiceDiagnosticoResultado();
    if (!r) {
      setDados(null);
      router.replace("/");
      return;
    }
    setDados(r);
    // Não limpar sessionStorage aqui: em React 18 Strict Mode o efeito roda 2x em dev e o segundo
    // mount perderia os dados. O próximo POST self-service sobrescreve a mesma chave.
  }, [router]);

  if (dados === undefined) {
    return (
      <div className="container max-w-lg py-16 text-center text-sm text-muted-foreground">Carregando…</div>
    );
  }

  if (dados === null) {
    return null;
  }

  const scoreValor =
    dados.score_geral !== null && dados.score_geral !== undefined && Number.isFinite(dados.score_geral)
      ? dados.score_geral
      : null;
  const scoreTexto = scoreValor !== null ? `${scoreValor.toFixed(1)} / 100` : "indisponível nesta resposta";
  const nivelTexto = rotuloNivelMaturidade(scoreValor);

  return (
    <div className="container max-w-xl py-10 px-4 space-y-8">
      <div className="flex justify-center">
        <div className="flex h-16 w-16 items-center justify-center rounded-full bg-accent/15 text-accent">
          <CheckCircle2 className="h-8 w-8" aria-hidden />
        </div>
      </div>

      <div className="text-center space-y-2">
        <h1 className="text-2xl font-bold tracking-tight md:text-3xl">Diagnóstico gravado na nuvem</h1>
        <p className="text-muted-foreground text-sm leading-relaxed max-w-md mx-auto">
          O questionário foi associado ao e-mail confirmado e armazenado no ambiente self-service. O painel
          completo (histórico, PDF, M12) continua ligado à conta B2B Tributiq, se desejar evoluir depois.
        </p>
      </div>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-lg">Resultado do diagnóstico</CardTitle>
          <CardDescription>Score e nível de maturidade tributária (mesmo critério do relatório)</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <p>
            <span className="font-medium text-foreground">Empresa:</span> {dados.empresa_razao_social}
          </p>
          <div className="rounded-lg border bg-muted/30 px-4 py-3 space-y-1">
            <p className="text-base font-semibold text-foreground tabular-nums">Score geral: {scoreTexto}</p>
            {nivelTexto ? (
              <p className="text-sm text-muted-foreground">
                Nível de maturidade:{" "}
                <span className="font-medium text-foreground">{nivelTexto}</span>
              </p>
            ) : (
              <p className="text-xs text-muted-foreground leading-relaxed">
                Se o score não aparecer, atualize a página ou confira a versão da API — o JSON deve incluir{" "}
                <span className="font-mono text-[11px]">score.score_geral.valor</span>.
              </p>
            )}
          </div>
          <p className="text-muted-foreground text-xs">
            Situação: <span className="font-medium text-foreground">{dados.status}</span>
            {" · "}
            ID: <span className="font-mono break-all">{dados.id}</span>
            {" · "}
            Relatório: {dados.locale_relatorio}
          </p>
        </CardContent>
        <CardFooter className="flex-col gap-2 sm:flex-row">
          <Button asChild className="w-full">
            <Link href="/">Voltar ao início</Link>
          </Button>
          <Button asChild variant="outline" className="w-full bg-transparent">
            <Link href="/login?redirect=/wizard">Entrar no painel B2B</Link>
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
}
