"use client";

import { useState } from "react";
import { ArchiveRestore } from "lucide-react";

import { Button } from "@/components/ui/button";
import { desarquivarEmpresaPainel } from "@/lib/api/arquivar_empresa_painel";

type Props = {
  cnpj14: string;
  razaoSocial: string;
  onDesarquivada?: (mensagem: string) => void;
  className?: string;
};

/**
 * Faixa de aviso + CTA quando a empresa está arquivada no painel.
 */
export function EmpresaPainelArquivoBanner({
  cnpj14,
  razaoSocial,
  onDesarquivada,
  className,
}: Props) {
  const [processando, setProcessando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  const desarquivar = async () => {
    setProcessando(true);
    setErro(null);
    try {
      const out = await desarquivarEmpresaPainel(cnpj14);
      onDesarquivada?.(out.mensagem);
    } catch (e) {
      setErro(e instanceof Error ? e.message : "Falha ao desarquivar.");
    } finally {
      setProcessando(false);
    }
  };

  return (
    <div
      className={
        className ??
        "rounded-lg border border-amber-500/40 bg-amber-500/10 px-4 py-3 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3"
      }
      role="status"
    >
      <div className="text-sm text-amber-950 dark:text-amber-100">
        <p className="font-medium">
          <strong>{razaoSocial}</strong> está arquivada no painel.
        </p>
        <p className="text-xs mt-1 opacity-90">
          Novos ciclos são gravados normalmente; ao concluir um diagnóstico a empresa volta à listagem
          principal. Pode também desarquivar agora.
        </p>
        {erro ? (
          <p className="text-xs text-destructive mt-2" role="alert">
            {erro}
          </p>
        ) : null}
      </div>
      <Button
        type="button"
        size="sm"
        variant="secondary"
        className="shrink-0"
        disabled={processando}
        onClick={() => void desarquivar()}
      >
        <ArchiveRestore className="h-4 w-4 mr-2" aria-hidden />
        {processando ? "A restaurar…" : "Desarquivar agora"}
      </Button>
    </div>
  );
}
