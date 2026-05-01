import { Button } from "@/components/ui/button";
import { ShieldCheck, BarChart3, FileText, ArrowRight } from "lucide-react";
import Link from "next/link";

export default function Home() {
  return (
    <div className="flex-1 flex flex-col items-center justify-center p-4 py-12 md:py-24">
      <div className="container max-w-4xl text-center space-y-8">
        
        <div className="space-y-4">
          <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight text-primary">
            QualiDiag<span className="text-accent">IQ</span>
          </h1>
          <p className="text-xl md:text-2xl text-muted-foreground font-medium max-w-2xl mx-auto">
            Descubra a maturidade e conformidade tributária da sua empresa frente à <strong className="text-foreground">Reforma do Consumo (EC 132/2023)</strong>.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row gap-4 justify-center py-6">
          <Button size="lg" asChild className="gap-2 text-md px-8 h-12 shadow-lg hover:shadow-xl transition-all">
            <Link href="/wizard">
              Iniciar Diagnóstico Gratuito
              <ArrowRight className="w-5 h-5" />
            </Link>
          </Button>
          <Button size="lg" variant="outline" className="text-md px-8 h-12" asChild>
            <Link href="/metodologia">Conhecer a Metodologia</Link>
          </Button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 text-left pt-12 border-t">
          
          <div className="space-y-3">
            <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center text-primary">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold">Baseado na ABNT NBR 17301</h3>
            <p className="text-muted-foreground text-sm">
              Avaliação algorítmica alinhada com os padrões de compliance e gestão tributária brasileiros mais recentes.
            </p>
          </div>
          
          <div className="space-y-3">
            <div className="w-12 h-12 bg-accent/10 rounded-lg flex items-center justify-center text-accent">
              <BarChart3 className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold">Score de Maturidade</h3>
            <p className="text-muted-foreground text-sm">
              Obtenha uma pontuação transparente (0-100) que indica o quão preparada sua empresa está para as novas regras de CBS e IBS.
            </p>
          </div>
          
          <div className="space-y-3">
            <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center text-primary">
              <FileText className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold">Relatório Executivo em PDF</h3>
            <p className="text-muted-foreground text-sm">
              Receba um diagnóstico completo em seu e-mail com identificação de gaps críticos e recomendações de especialistas.
            </p>
          </div>
          
        </div>
      </div>
    </div>
  );
}
