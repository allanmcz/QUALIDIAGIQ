"use client";

import { createPortal } from "react-dom";

import { Button } from "@/components/ui/button";

export type WizardCacheResumeOverlayProps = {
  cacheResumePrompt: { hasDraft: boolean; hasPending: boolean };
  onContinuar: () => void;
  onReiniciar: () => void;
};

export function WizardCacheResumeOverlay({
  cacheResumePrompt,
  onContinuar,
  onReiniciar,
}: WizardCacheResumeOverlayProps) {
  return createPortal(
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 p-4">
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="qdi-wizard-resume-title"
        className="pointer-events-auto w-full max-w-md space-y-4 rounded-xl border border-border bg-card p-6 text-card-foreground shadow-xl"
      >
        <h2 id="qdi-wizard-resume-title" className="text-lg font-semibold text-foreground">
          Diagnóstico em andamento neste navegador
        </h2>
        <p className="text-sm leading-relaxed text-muted-foreground">
          Há um diagnóstico em andamento neste navegador. O resultado final fica disponível após confirmação por
          e-mail. Deseja continuar de onde parou ou iniciar um novo diagnóstico do zero?
        </p>
        <ul className="list-disc space-y-1 pl-5 text-sm text-muted-foreground">
          {cacheResumePrompt.hasDraft ? <li>Respostas já preenchidas no assistente.</li> : null}
          {cacheResumePrompt.hasPending ? (
            <li>
              Resultado aguardando confirmação por e-mail.
            </li>
          ) : null}
        </ul>
        {cacheResumePrompt.hasDraft && cacheResumePrompt.hasPending ? (
          <p className="text-xs leading-snug text-muted-foreground">
            «Continuar» restaura o rascunho do assistente. O envio pendente permanece guardado até você concluir o fluxo
            de cadastro/login ou reiniciar.
          </p>
        ) : null}
        <p className="text-xs leading-snug text-muted-foreground">
          LGPD: estes dados ficam apenas no seu dispositivo até você confirmar ou salvar o diagnóstico na plataforma.
        </p>
        <div className="flex flex-col-reverse gap-2 pt-2 sm:flex-row sm:justify-end">
          <Button type="button" variant="outline" onClick={onReiniciar}>
            Reiniciar diagnóstico
          </Button>
          <Button type="button" onClick={() => void onContinuar()}>
            Continuar
          </Button>
        </div>
      </div>
    </div>,
    document.body,
  );
}
