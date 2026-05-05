"use client";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { TOTAL_STEPS } from "@/lib/wizard/wizardFormDefaults";

export type WizardNavigationButtonsProps = {
  step: number;
  isSubmitting: boolean;
  catalogLoading: boolean;
  totalPerguntas: number;
  ultimaPerguntaDoQuestionario: boolean;
  hasToken: boolean;
  voltarWizard: () => void;
  nextStep: () => Promise<void>;
  seguirOuFinalizarQuestionario: () => Promise<void>;
  larguraCheiaEmMobile: boolean;
};

export function WizardNavigationButtons({
  step,
  isSubmitting,
  catalogLoading,
  totalPerguntas,
  ultimaPerguntaDoQuestionario,
  hasToken,
  voltarWizard,
  nextStep,
  seguirOuFinalizarQuestionario,
  larguraCheiaEmMobile,
}: WizardNavigationButtonsProps) {
  const clsBotao = cn(larguraCheiaEmMobile && "w-full sm:w-auto shrink-0");
  return (
    <>
      <Button
        type="button"
        variant="outline"
        onClick={voltarWizard}
        disabled={step === 1 || isSubmitting}
        className={clsBotao}
      >
        Voltar
      </Button>

      {step < TOTAL_STEPS ? (
        <Button
          type="button"
          onClick={() => void nextStep()}
          disabled={catalogLoading}
          className={clsBotao}
        >
          {catalogLoading ? "Carregando perguntas…" : "Próxima Etapa"}
        </Button>
      ) : (
        <Button
          type="button"
          onClick={() => void seguirOuFinalizarQuestionario()}
          disabled={isSubmitting || totalPerguntas === 0}
          className={cn("bg-accent text-accent-foreground hover:bg-accent/90", clsBotao)}
        >
          {isSubmitting
            ? "Enviando…"
            : ultimaPerguntaDoQuestionario && !hasToken
              ? "Gerar diagnóstico"
              : ultimaPerguntaDoQuestionario
                ? "Finalizar Diagnóstico"
                : "Seguir"}
        </Button>
      )}
    </>
  );
}
