"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { ChevronDown, ExternalLink, LayoutGrid } from "lucide-react";

import { Button } from "@/components/ui/button";
import { buildPlanoAcaoFichaHref } from "@/lib/dashboard/plano_acao_ficha_urls";
import { cn } from "@/lib/utils";

type Props = {
  cnpj14: string;
  diagnosticoId: string;
  planoAcaoId: string;
  razaoSocial?: string;
  disabled?: boolean;
  className?: string;
};

/**
 * Menu «Ações» da grelha — atalho para a ficha dedicada e âncora do Kanban.
 */
export function PlanoAcaoAcoesMenu({
  cnpj14,
  diagnosticoId,
  planoAcaoId,
  razaoSocial,
  disabled,
  className,
}: Props) {
  const [aberto, setAberto] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  const fichaHref = buildPlanoAcaoFichaHref(cnpj14, planoAcaoId, {
    diagnosticoId,
    razaoSocial,
    hashVolta: "empresa-quadro-implantacao-principal",
  });

  useEffect(() => {
    if (!aberto) return;
    const fechar = (ev: MouseEvent) => {
      if (ref.current && !ref.current.contains(ev.target as Node)) setAberto(false);
    };
    const onKey = (ev: KeyboardEvent) => {
      if (ev.key === "Escape") setAberto(false);
    };
    document.addEventListener("mousedown", fechar);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", fechar);
      document.removeEventListener("keydown", onKey);
    };
  }, [aberto]);

  return (
    <div ref={ref} className={cn("relative inline-block", className)}>
      <Button
        type="button"
        variant="outline"
        size="sm"
        className="h-8 gap-1 text-xs w-full justify-between"
        disabled={disabled}
        aria-expanded={aberto}
        aria-haspopup="menu"
        onClick={() => setAberto((v) => !v)}
      >
        Ações
        <ChevronDown className="h-3.5 w-3.5 opacity-70" aria-hidden />
      </Button>
      {aberto ? (
        <div
          role="menu"
          className="absolute right-0 z-50 mt-1 min-w-[12rem] rounded-md border bg-popover p-1 shadow-md text-sm"
        >
          <Link
            role="menuitem"
            href={fichaHref}
            className="flex items-center gap-2 rounded-sm px-2 py-1.5 hover:bg-accent"
            onClick={() => setAberto(false)}
          >
            <ExternalLink className="h-3.5 w-3.5 shrink-0" aria-hidden />
            Abrir ficha da ação
          </Link>
          <a
            role="menuitem"
            href="#empresa-kanban-plano-titulo"
            className="flex items-center gap-2 rounded-sm px-2 py-1.5 hover:bg-accent"
            onClick={() => setAberto(false)}
          >
            <LayoutGrid className="h-3.5 w-3.5 shrink-0" aria-hidden />
            Ver no Kanban
          </a>
        </div>
      ) : null}
    </div>
  );
}
