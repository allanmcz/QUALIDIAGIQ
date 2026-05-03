import { HeroIllustration } from "@/components/brand/HeroIllustration";
import { Button } from "@/components/ui/button";
import { ShieldCheck, BarChart3, FileText, ArrowRight, LogIn } from "lucide-react";
import Link from "next/link";

export default function Home() {
  return (
    <div className="flex-1 flex flex-col items-center p-4 py-12 md:py-20">
      <section className="container max-w-6xl w-full">
        <div className="grid grid-cols-1 gap-10 md:grid-cols-12 md:items-center md:gap-12">
          <div className="space-y-8 text-center md:col-span-7 md:text-left">
            <div className="space-y-4">
              <h1 className="text-4xl font-extrabold tracking-tight text-primary md:text-5xl lg:text-6xl">
                QualiDiag<span className="text-accent">IQ</span>
              </h1>
              <p className="mx-auto max-w-2xl text-xl font-medium text-muted-foreground md:mx-0 md:text-2xl">
                Descubra a maturidade e conformidade tributária da sua empresa frente à{" "}
                <strong className="text-foreground">Reforma do Consumo (EC 132/2023)</strong>.
              </p>
            </div>

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
              <Button size="lg" variant="outline" className="gap-2 px-8 text-md h-12" asChild>
                <Link href="/login?redirect=/dashboard">
                  <LogIn className="h-5 w-5 shrink-0" aria-hidden />
                  Entrar no painel B2B
                </Link>
              </Button>
              <Button size="lg" variant="outline" className="px-8 text-md h-12" asChild>
                <Link href="/metodologia">Conhecer a Metodologia</Link>
              </Button>
            </div>
            <p className="mx-auto max-w-xl text-center text-sm text-muted-foreground md:mx-0 md:text-left">
              Conta corporativa Tributiq: consulte histórico, PDF e checklist{" "}
              <span className="whitespace-nowrap">sem iniciar</span> um novo diagnóstico neste momento.
            </p>
          </div>

          <div className="md:col-span-5">
            <HeroIllustration variant="radar" priority />
          </div>
        </div>
      </section>

      <div className="container max-w-4xl border-t pt-12 mt-4 md:mt-16">
        <div className="grid grid-cols-1 gap-8 pt-4 text-left md:grid-cols-3">
          <div className="space-y-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <ShieldCheck className="h-6 w-6" />
            </div>
            <h3 className="text-lg font-bold">Baseado na ABNT NBR 17301</h3>
            <p className="text-sm text-muted-foreground">
              Avaliação algorítmica alinhada com os padrões de compliance e gestão tributária brasileiros mais
              recentes.
            </p>
          </div>

          <div className="space-y-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-accent/10 text-accent">
              <BarChart3 className="h-6 w-6" />
            </div>
            <h3 className="text-lg font-bold">Score de Maturidade</h3>
            <p className="text-sm text-muted-foreground">
              Obtenha uma pontuação transparente (0-100) que indica o quão preparada sua empresa está para as novas
              regras de CBS e IBS.
            </p>
          </div>

          <div className="space-y-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <FileText className="h-6 w-6" />
            </div>
            <h3 className="text-lg font-bold">Relatório Executivo em PDF</h3>
            <p className="text-sm text-muted-foreground">
              Receba um diagnóstico completo em seu e-mail com identificação de gaps críticos e recomendações de
              especialistas.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
