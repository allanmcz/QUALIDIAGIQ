"use client";

import Link from "next/link";
import { Info } from "lucide-react";
import type { Control, UseFormRegister } from "react-hook-form";

import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { WizardPerguntaInput } from "@/components/wizard/WizardPerguntaInput";
import { postValidarAncora } from "@/lib/api/normativa";
import type { PerguntaCatalogo } from "@/lib/api/questionario";
import type { DiagnosticoPayloadFormInput } from "@/lib/schemas/wizard";
import { normativaWizardPainelAtivo } from "@/lib/wizard/wizardEnv";
import { tipoEhEscalaLikert15, tipoEhNumericaWizard } from "@/lib/wizard/perguntaTipo";

export type WizardStepQuestionarioProps = {
  apiError: string | null;
  perguntas: PerguntaCatalogo[];
  indicePerguntaAtual: number;
  totalPerguntas: number;
  normaTexto: string;
  setNormaTexto: (v: string) => void;
  normaFeedback: string | null;
  setNormaFeedback: (v: string | null) => void;
  normaCarregando: boolean;
  setNormaCarregando: (v: boolean) => void;
  register: UseFormRegister<DiagnosticoPayloadFormInput>;
  control: Control<DiagnosticoPayloadFormInput>;
};

export function WizardStepQuestionario({
  apiError,
  perguntas,
  indicePerguntaAtual,
  totalPerguntas,
  normaTexto,
  setNormaTexto,
  normaFeedback,
  setNormaFeedback,
  normaCarregando,
  setNormaCarregando,
  register,
  control,
}: WizardStepQuestionarioProps) {
  return (
    <div className="flex min-h-0 flex-1 flex-col gap-3 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="shrink-0 space-y-2">
        {normativaWizardPainelAtivo() && (
          <div data-testid="wizard-p8-normativa" className="rounded-lg border bg-muted/10 p-3 space-y-2">
            <p className="text-sm font-semibold text-foreground">
              P8 — Protótipo: checagem leve de redação normativa (não é Lexiq / RAG completo)
            </p>
            <p className="text-xs text-muted-foreground leading-relaxed">
              Ferramenta didática apenas: heurísticas simples sobre citações (ex.: LC 214/2025, EC 132/2023). Não gera
              parecer jurídico, não substitui análise profissional e não garante suficiência perante auditorias formais
              (LC 214/2025 — boa fé informacional ao contribuinte). Endpoint{" "}
              <span className="font-mono">POST /normativa/validar-ancora</span> sem login.
            </p>
            <textarea
              value={normaTexto}
              onChange={(e) => setNormaTexto(e.target.value)}
              rows={3}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              placeholder="Ex.: Esta prática deve ser revisada conforme LC 214/2025 art. 5º."
            />
            <div className="flex gap-2 items-center flex-wrap">
              <Button
                type="button"
                variant="secondary"
                size="sm"
                disabled={normaCarregando || normaTexto.trim().length < 3}
                onClick={async () => {
                  setNormaFeedback(null);
                  setNormaCarregando(true);
                  try {
                    const r = await postValidarAncora(normaTexto.trim());
                    setNormaFeedback(
                      r.valido ? "Aceito — âncora normativa reconhecível." : (r.motivo_rejeicao ?? "Sem âncora."),
                    );
                  } catch (err) {
                    setNormaFeedback(err instanceof Error ? err.message : "Erro ao validar.");
                  } finally {
                    setNormaCarregando(false);
                  }
                }}
              >
                {normaCarregando ? "Validando…" : "Validar texto"}
              </Button>
              {normaFeedback && (
                <span className="text-xs text-muted-foreground" role="status">
                  {normaFeedback}
                </span>
              )}
            </div>
          </div>
        )}
        {apiError && (
          <div className="px-3 py-2 bg-destructive/10 border border-destructive/20 text-destructive rounded-md text-xs md:text-sm">
            {apiError}
          </div>
        )}
        <details className="rounded-md border bg-muted/30 px-3 py-2 text-xs shrink-0 group">
          <summary className="cursor-pointer font-medium text-muted-foreground list-none flex items-center gap-2 select-none [&::-webkit-details-marker]:hidden">
            <span aria-hidden className="text-[10px] opacity-70 group-open:rotate-90 transition-transform">
              ▸
            </span>
            Metodologia e transparência (links)
          </summary>
          <div className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-muted-foreground pt-1 border-t border-border/50">
            <Link href="/abnt-framework" className="text-primary underline font-medium">
              Framework ABNT (guia)
            </Link>
            <Link href="/metodologia" className="text-primary underline font-medium">
              Metodologia e pesos
            </Link>
          </div>
        </details>
      </div>
      {totalPerguntas > 0 && indicePerguntaAtual < totalPerguntas && (
        <div
          key={perguntas[indicePerguntaAtual].id}
          data-testid="wizard-pergunta-atual"
          className="mx-auto flex min-h-0 w-full max-w-xl flex-col justify-start space-y-3 rounded-lg border bg-muted/20 p-4 sm:p-5"
        >
          <p role="status" aria-live="polite" aria-atomic="true" className="text-sm font-medium text-muted-foreground">
            Pergunta {indicePerguntaAtual + 1} de {totalPerguntas}
          </p>
          <div className="flex items-start gap-2">
            <Label className="text-base font-semibold text-foreground/90 leading-tight block flex-1 min-w-0">
              {indicePerguntaAtual + 1}. {perguntas[indicePerguntaAtual].texto}{" "}
              <span className="text-muted-foreground font-normal text-xs">
                ({perguntas[indicePerguntaAtual].codigo})
              </span>
            </Label>
            {perguntas[indicePerguntaAtual].base_legal ? (
              <Tooltip>
                <TooltipTrigger asChild>
                  <button
                    type="button"
                    className="mt-0.5 shrink-0 rounded-md p-1 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    aria-label={`Base legal: ${perguntas[indicePerguntaAtual].base_legal}`}
                  >
                    <Info className="h-5 w-5" aria-hidden />
                  </button>
                </TooltipTrigger>
                <TooltipContent side="left" className="max-w-xs text-left leading-snug">
                  <span className="font-medium text-foreground">Base legal (referência)</span>
                  <span className="mt-1 block text-muted-foreground">
                    {perguntas[indicePerguntaAtual].base_legal}
                  </span>
                </TooltipContent>
              </Tooltip>
            ) : null}
          </div>
          {tipoEhEscalaLikert15(perguntas[indicePerguntaAtual].tipo) && (
            <p className="text-sm text-muted-foreground leading-snug">
              Escala Likert (1 a 5): 1 = menor aderência, 5 = maior aderência à prática perguntada. É obrigatório
              escolher um nível — não há valor por defeito; não é possível avançar sem marcar uma opção.
            </p>
          )}
          {tipoEhNumericaWizard(perguntas[indicePerguntaAtual].tipo) && (
            <p className="text-sm text-muted-foreground leading-snug">
              Escala numérica: informe um inteiro de 0 a 100 (conforme o enunciado).
            </p>
          )}
          <WizardPerguntaInput
            pergunta={perguntas[indicePerguntaAtual]}
            index={indicePerguntaAtual}
            register={register}
            control={control}
          />
        </div>
      )}
    </div>
  );
}
