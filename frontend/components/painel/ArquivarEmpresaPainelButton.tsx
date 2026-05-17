"use client";

import { useState } from "react";
import { Archive, ArchiveRestore } from "lucide-react";

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
import { patchArquivarEmpresaPainel } from "@/lib/api/arquivar_empresa_painel";

type Props = {
  cnpj14: string;
  razaoSocial: string;
  /** Se true, o diálogo oferece restaurar em vez de arquivar. */
  arquivada?: boolean;
  onConcluido?: (mensagem: string) => void;
  variant?: "outline" | "secondary" | "ghost";
  className?: string;
};

function mascaraCnpj(d: string): string {
  return d.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/, "$1.$2.$3/$4-$5");
}

/**
 * Arquivar ou restaurar empresa na listagem do painel (não apaga diagnósticos WORM).
 */
export function ArquivarEmpresaPainelButton({
  cnpj14,
  razaoSocial,
  arquivada = false,
  onConcluido,
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
      const out = await patchArquivarEmpresaPainel(cnpj14, !arquivada);
      setAberto(false);
      onConcluido?.(out.mensagem);
    } catch (e) {
      setErro(e instanceof Error ? e.message : "Falha ao atualizar arquivo da empresa.");
    } finally {
      setProcessando(false);
    }
  };

  const titulo = arquivada ? "Restaurar empresa no painel?" : "Arquivar empresa no painel?";
  const gatilho = arquivada ? "Restaurar no painel" : "Arquivar empresa";
  const Icon = arquivada ? ArchiveRestore : Archive;

  return (
    <Dialog open={aberto} onOpenChange={setAberto}>
      <DialogTrigger asChild>
        <Button
          type="button"
          variant={variant}
          className={className}
          onClick={() => setErro(null)}
        >
          <Icon className="h-4 w-4 mr-2" aria-hidden />
          {gatilho}
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{titulo}</DialogTitle>
          <DialogDescription className="sr-only">
            Arquivo operacional da empresa no painel de diagnósticos.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-3 text-sm text-muted-foreground">
          {arquivada ? (
            <p>
              <strong className="text-foreground">{razaoSocial}</strong> (CNPJ{" "}
              {mascaraCnpj(cnpj14)}) voltará a aparecer na listagem principal do painel.
            </p>
          ) : (
            <>
              <p>
                <strong className="text-foreground">{razaoSocial}</strong> (CNPJ{" "}
                {mascaraCnpj(cnpj14)}) deixará de aparecer na listagem principal. Os diagnósticos
                <strong className="text-foreground"> finalizados</strong> permanecem na base (evidência
                auditável).
              </p>
              <p>
                Para remover ciclos em andamento ou expirados, abra a empresa e use{" "}
                <strong className="text-foreground">Remover ciclos não finalizados</strong>.
              </p>
            </>
          )}
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
          <Button type="button" variant={arquivada ? "default" : "secondary"} disabled={processando} onClick={() => void confirmar()}>
            {processando ? "A processar…" : "Confirmar"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
