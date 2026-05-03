import { CheckCircle2, ArrowRight, LayoutDashboard } from "lucide-react";
import { Button } from "@/components/ui/button";
import Link from "next/link";

export const metadata = {
  title: "Sucesso | QualiDiagIQ",
};

export default function SucessoPage() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center bg-muted/10 p-4 py-16">
      <div className="container max-w-2xl space-y-8 rounded-2xl border bg-card p-8 text-center shadow-lg md:p-12">
        <div className="flex justify-center">
          <div className="flex h-20 w-20 items-center justify-center rounded-full bg-accent/10 text-accent animate-in zoom-in duration-500">
            <CheckCircle2 className="h-10 w-10" />
          </div>
        </div>

        <div className="space-y-4">
          <h1 className="text-3xl font-bold text-primary">Fase 1 concluída — diagnóstico gravado na API</h1>
          <p className="text-lg text-muted-foreground">
            O score de maturidade tributária foi processado e persistido no tenant autenticado. Relatório PDF,
            recomendações e trilha no painel seguem as regras do seu ambiente (e-mail quando configurado).
          </p>
        </div>

        <div className="space-y-4 border-t border-border pt-8 text-left">
          <h2 className="text-center text-xl font-semibold text-foreground">Fase 2 — após cadastro e login</h2>
          <p className="text-center text-sm leading-relaxed text-muted-foreground">
            O acesso completo ao painel consultor (histórico, detalhe por diagnóstico, checklist M12, etc.)
            permanece ligado à sua conta na plataforma Tributiq. Se ainda não tiver cadastro, utilize o
            canal acordado com o time Tributiq.
          </p>
          <div className="flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Button asChild size="lg" className="w-full gap-2 sm:w-auto">
              <Link href="/dashboard">
                <LayoutDashboard className="h-4 w-4" />
                Abrir painel (fase 2)
              </Link>
            </Button>
            <Button asChild variant="outline" size="lg" className="w-full sm:w-auto">
              <Link href="/login">Entrar com outra conta</Link>
            </Button>
          </div>
        </div>

        <div className="flex justify-center pt-2">
          <Button asChild variant="ghost" size="lg" className="gap-2">
            <Link href="/">
              Voltar ao início
              <ArrowRight className="h-4 w-4" />
            </Link>
          </Button>
        </div>
      </div>
    </div>
  );
}
