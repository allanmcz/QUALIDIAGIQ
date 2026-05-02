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
  clearSelfServiceDiagnosticoResultado,
  loadSelfServiceDiagnosticoResultado,
  type SelfServiceDiagnosticoResultado,
} from "@/lib/wizard/self_service_result";

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
    clearSelfServiceDiagnosticoResultado();
  }, [router]);

  if (dados === undefined) {
    return (
      <div className="container max-w-lg py-16 text-center text-sm text-muted-foreground">Carregando…</div>
    );
  }

  if (dados === null) {
    return null;
  }

  const scoreTexto =
    dados.score_geral !== null && dados.score_geral !== undefined
      ? `${dados.score_geral.toFixed(1)} / 100`
      : "em processamento";

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
          <CardTitle className="text-lg">Resumo</CardTitle>
          <CardDescription>Identificador e score calculado pela API</CardDescription>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <p>
            <span className="font-medium text-foreground">Empresa:</span> {dados.empresa_razao_social}
          </p>
          <p>
            <span className="font-medium text-foreground">Score geral:</span>{" "}
            <span className="tabular-nums">{scoreTexto}</span>
          </p>
          <p className="text-muted-foreground text-xs">
            ID: <span className="font-mono break-all">{dados.id}</span> · idioma relatório:{" "}
            {dados.locale_relatorio}
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
