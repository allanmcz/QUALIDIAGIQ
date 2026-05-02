import { WizardForm } from "@/components/wizard/WizardForm";
import { ShieldCheck } from "lucide-react";

export const metadata = {
  title: "Diagnóstico ABNT NBR 17301 | QualiDiagIQ",
};

export default function WizardPage() {
  return (
    <div className="flex min-h-0 flex-1 flex-col bg-muted/10 px-4 pb-[max(2.5rem,env(safe-area-inset-bottom,0px))] pt-4 md:px-4 md:pb-12 md:pt-8">
      <div className="container mx-auto flex min-h-0 flex-1 flex-col gap-4 max-w-4xl md:gap-5">
        <div className="text-center space-y-2 shrink-0">
          <div className="inline-flex items-center justify-center p-2 bg-accent/10 rounded-full text-accent mb-1">
            <ShieldCheck className="w-5 h-5 md:w-6 md:h-6" />
          </div>
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight">
            Análise de Maturidade Tributária
          </h1>
          <p className="text-muted-foreground text-sm md:text-base max-w-2xl mx-auto leading-snug">
            Diagnóstico em 3 passos — Reforma do Consumo e ABNT NBR 17301:2026.
          </p>
        </div>

        <div className="flex flex-col flex-1 min-h-0">
          <WizardForm />
        </div>
        
      </div>
    </div>
  );
}
