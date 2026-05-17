"use client";

import Link from "next/link";
import { useState } from "react";
import { Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { deleteDiagnosticosEmpresaPainel } from "@/lib/api/eliminar_empresa_diagnosticos";

type Props = {
  cnpj14: string;
  razaoSocial: string;
  onExcluido?: (mensagem: string) => void;
  variant?: "outline" | "destructive" | "ghost";
  className?: string;
};

function mascaraCnpj(d: string): string {
  return d.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/, "$1.$2.$3/$4-$5");
}

/**
 * Remove ciclos não finalizados (em andamento, cancelado, expirado) — vista da empresa.
 */
export function ExcluirCiclosElegiveisEmpresaButton({
  cnpj14,
  razaoSocial,
  onExcluido,
  variant = "outline",
  className,
}: Props) {
  const [aberto, setAberto] = useState(false);
  const [processando, setProcessando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  const confirmar = async () => {
    setProcessando(true);
    setErro(null);
    try {
      const out = await deleteDiagnosticosEmpresaPainel(cnpj14);
      setAberto(false);
      onExcluido?.(out.mensagem);
    } catch (e) {
      setErro(e instanceof Error ? e.message : "Falha ao remover ciclos.");
    } finally {
      setProcessando(false);
    }
  };

  return (
    <Dialog open={aberto} onOpenChange={setAberto}>
      <DialogTrigger asChild>
        <Button
          type="button"
          variant={variant}
          className={className}
          onClick={() => setErro(null)}
        >
          <Trash2 className="h-4 w-4 mr-2" aria-hidden />
          Remover ciclos não finalizados
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Remover ciclos não finalizados?</DialogTitle>
          <DialogDescription className="sr-only">
            Exclusão física de diagnósticos elegíveis desta empresa.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-3 text-sm text-muted-foreground">
          <p>
            Serão removidos <strong className="text-foreground">todos os diagnósticos não finalizados</strong> de{" "}
            <strong className="text-foreground">{razaoSocial}</strong> (CNPJ {mascaraCnpj(cnpj14)}). Esta ação não
            pode ser desfeita.
          </p>
          <p>
            Ciclos <strong className="text-foreground">finalizados</strong> permanecem (evidência WORM). Para esses,
            use{" "}
            <Link href="/dashboard/privacidade" className="text-primary underline">
              Privacidade LGPD
            </Link>
            .
          </p>
        </div>
        {erro ? (
          <p className="text-sm text-destructive" role="alert">
            {erro}
          </p>
        ) : null}
        <DialogFooter className="gap-2 sm:gap-0">
          <Button type="button" variant="outline" disabled={processando} onClick={() => setAberto(false)}>
            Cancelar
          </Button>
          <Button type="button" variant="destructive" disabled={processando} onClick={() => void confirmar()}>
            {processando ? "Removendo…" : "Confirmar remoção"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
