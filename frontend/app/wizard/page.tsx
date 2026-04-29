import { WizardForm } from "@/components/wizard/WizardForm";
import { ShieldCheck } from "lucide-react";

export const metadata = {
  title: "Diagnóstico ABNT NBR 17301 | QualiDiagIQ",
};

export default function WizardPage() {
  return (
    <div className="flex-1 flex flex-col p-4 py-8 md:py-16 bg-muted/10">
      <div className="container max-w-4xl mx-auto space-y-8">
        
        <div className="text-center space-y-2">
          <div className="inline-flex items-center justify-center p-2 bg-accent/10 rounded-full text-accent mb-2">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <h1 className="text-3xl md:text-4xl font-bold tracking-tight">
            Análise de Maturidade Tributária
          </h1>
          <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
            Descubra em 3 passos simples o nível de aderência da sua empresa às novas normas e identifique pontos críticos de melhoria.
          </p>
        </div>

        <WizardForm />
        
      </div>
    </div>
  );
}
