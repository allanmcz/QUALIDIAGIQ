"use client";

import Link from "next/link";
import { ArrowRight, LayoutDashboard, LogIn } from "lucide-react";

import { Button } from "@/components/ui/button";
import { useSessaoB2bLogado } from "@/lib/auth/use_sessao_b2b_logado";

/**
 * Fila de CTAs do hero na landing + texto de apoio (sessão B2B reactiva).
 */
export function HomeHeroCtas() {
  const logado = useSessaoB2bLogado();

  return (
    <div className="space-y-3">
      <div className="flex flex-col justify-center gap-3 sm:flex-row sm:flex-wrap md:justify-start">
        <Button
          size="lg"
          asChild
          className="gap-2 px-8 text-md h-12 shadow-lg transition-all hover:shadow-xl"
        >
          <Link href="/wizard">
            Iniciar Diagnóstico Gratuito
            <ArrowRight className="h-5 w-5" />
          </Link>
        </Button>

        {logado === undefined ? (
          <Button size="lg" variant="outline" className="gap-2 px-8 text-md h-12" disabled aria-busy={true}>
            …
          </Button>
        ) : logado ? (
          <Button size="lg" variant="outline" className="gap-2 px-8 text-md h-12" asChild>
            <Link href="/dashboard">
              <LayoutDashboard className="h-5 w-5 shrink-0" aria-hidden />
              Painel
            </Link>
          </Button>
        ) : (
          <Button size="lg" variant="outline" className="gap-2 px-8 text-md h-12" asChild>
            <Link href="/login?redirect=/dashboard">
              <LogIn className="h-5 w-5 shrink-0" aria-hidden />
              Entrar
            </Link>
          </Button>
        )}

        <Button size="lg" variant="outline" className="px-8 text-md h-12" asChild>
          <Link href="/metodologia">Conhecer a Metodologia</Link>
        </Button>
      </div>

      {logado === undefined ? (
        <p className="mx-auto min-h-[2.75rem] max-w-xl text-center text-sm text-muted-foreground/60 md:mx-0 md:text-left">
          …
        </p>
      ) : logado ? (
        <p className="mx-auto max-w-xl text-center text-sm text-muted-foreground md:mx-0 md:text-left">
          Sessão iniciada: use <strong className="text-foreground">Painel</strong> para histórico, PDF e checklist — ou
          inicie um novo diagnóstico acima.
        </p>
      ) : (
        <p className="mx-auto max-w-xl text-center text-sm text-muted-foreground md:mx-0 md:text-left">
          Conta corporativa Tributiq: consulte histórico, PDF e checklist{" "}
          <span className="whitespace-nowrap">sem iniciar</span> um novo diagnóstico neste momento.
        </p>
      )}
    </div>
  );
}
