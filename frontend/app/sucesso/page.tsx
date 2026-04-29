import { CheckCircle2, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import Link from "next/link";

export const metadata = {
  title: "Sucesso | QualiDiagIQ",
};

export default function SucessoPage() {
  return (
    <div className="flex-1 flex flex-col items-center justify-center p-4 py-16 bg-muted/10">
      <div className="container max-w-2xl text-center space-y-8 bg-card border shadow-lg rounded-2xl p-8 md:p-12">
        
        <div className="flex justify-center">
          <div className="w-20 h-20 bg-accent/10 rounded-full flex items-center justify-center text-accent animate-in zoom-in duration-500">
            <CheckCircle2 className="w-10 h-10" />
          </div>
        </div>

        <div className="space-y-4">
          <h1 className="text-3xl font-bold text-primary">
            Diagnóstico Concluído com Sucesso!
          </h1>
          <p className="text-lg text-muted-foreground">
            O seu Score de Maturidade Tributária foi processado. O relatório completo em PDF, contendo suas notas ABNT NBR 17301 e nossas recomendações executivas, foi enviado para o seu e-mail.
          </p>
        </div>

        <div className="pt-6">
          <Button asChild size="lg" className="w-full sm:w-auto">
            <Link href="/" className="gap-2">
              Voltar ao Início
              <ArrowRight className="w-4 h-4" />
            </Link>
          </Button>
        </div>
        
      </div>
    </div>
  );
}
