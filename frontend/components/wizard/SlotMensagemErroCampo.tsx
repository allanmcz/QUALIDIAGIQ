"use client";

import type { ReactNode } from "react";

/**
 * Reserva linha para erro de validação — evita que uma coluna “puxe” o alinhamento vertical
 * do grid quando só um campo falha (ex.: Porte × Regime).
 */
export function SlotMensagemErroCampo({ children }: { children?: ReactNode }) {
  return (
    <div className="min-h-[1.375rem] text-sm leading-tight text-destructive" aria-live="polite">
      {children}
    </div>
  );
}
