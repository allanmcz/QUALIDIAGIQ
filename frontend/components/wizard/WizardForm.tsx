"use client";

import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { WizardCacheResumeOverlay } from "@/components/wizard/WizardCacheResumeOverlay";
import { WizardNavigationButtons } from "@/components/wizard/WizardNavigationButtons";
import { WizardStepIdentificacao } from "@/components/wizard/steps/WizardStepIdentificacao";
import { WizardStepPerfilEmpresa } from "@/components/wizard/steps/WizardStepPerfilEmpresa";
import { WizardStepQuestionario } from "@/components/wizard/steps/WizardStepQuestionario";
import { useWizardState } from "@/components/wizard/useWizardState";
import { cn } from "@/lib/utils";
import { TOTAL_STEPS } from "@/lib/wizard/wizardFormDefaults";

/**
 * Orquestrador do assistente de diagnóstico — estado em `useWizardState`, JSX por passo (W3/W4).
 */
export function WizardForm() {
  const w = useWizardState();

  const navProps = {
    step: w.step,
    isSubmitting: w.isSubmitting,
    catalogLoading: w.catalogLoading,
    totalPerguntas: w.totalPerguntas,
    ultimaPerguntaDoQuestionario: w.ultimaPerguntaDoQuestionario,
    hasToken: w.hasToken,
    voltarWizard: w.voltarWizard,
    nextStep: w.nextStep,
    seguirOuFinalizarQuestionario: w.seguirOuFinalizarQuestionario,
  };

  return (
    <>
      {w.cacheResumePrompt != null && (
        <WizardCacheResumeOverlay
          cacheResumePrompt={w.cacheResumePrompt}
          onContinuar={w.handleCacheContinuar}
          onReiniciar={w.handleCacheReiniciar}
        />
      )}
      <div
        className={cn(
          "w-full max-w-3xl mx-auto flex flex-col min-h-0",
          w.step === 3 ? "flex-1 gap-3" : "space-y-6",
          w.cacheResumePrompt != null && "pointer-events-none opacity-60",
        )}
      >
        <div className={cn("w-full min-w-0 space-y-2", w.step === 3 && "shrink-0")}>
          <div className="flex w-full justify-between gap-4 text-sm text-muted-foreground font-medium">
            <span className="min-w-0 truncate">
              Passo {w.step} de {TOTAL_STEPS}
            </span>
            <span className="shrink-0 tabular-nums">{Math.round(w.progressBarPercent)}% Concluído</span>
          </div>
          <Progress value={w.progressBarPercent} className="w-full" />
        </div>

        <div
          className={cn(
            w.step === 3 &&
              "flex min-h-0 w-full flex-1 flex-col overflow-hidden rounded-xl border border-primary/10 bg-card text-sm shadow-lg ring-1 ring-foreground/10",
            w.step !== 3 && "contents",
          )}
        >
          <Card
            className={cn(
              "min-h-0",
              w.step === 3
                ? "flex flex-1 flex-col gap-0 overflow-hidden rounded-none border-0 bg-transparent py-0 text-card-foreground shadow-none ring-0"
                : "overflow-visible border-primary/10 shadow-lg",
            )}
          >
            <CardHeader
              className={cn(
                "space-y-1 bg-muted/30 border-b shrink-0",
                w.step === 3 ? "py-3 md:py-4" : "px-6 pb-4 pt-6 sm:px-6",
              )}
            >
              <CardTitle className={cn("text-primary", w.step === 3 ? "text-xl md:text-2xl" : "text-2xl")}>
                {w.step === 1 && "Identificação Inicial"}
                {w.step === 2 && "Perfil da Empresa"}
                {w.step === 3 && "Questionário adaptativo (Reforma + ABNT NBR 17301)"}
              </CardTitle>
              <CardDescription className={cn(w.step === 3 && "text-xs md:text-sm leading-snug")}>
                {w.step === 1 &&
                  "Cadastro da empresa: CNPJ é opcional (se informado, validamos DV e vinculamos à PJ). Razão social é obrigatória. Cada diagnóstico gera um registro próprio (histórico e quadro por ID). Responder ao assistente não exige sessão. Para gravar na nuvem **sem** conta na plataforma: confirme o **e-mail** com o código enviado (OTP) — o resultado fica ligado a esse e-mail; depois de **cadastrar ou entrar**, pode vincular esses registos à sua empresa. Com **sessão já iniciada** na plataforma, a gravação é direta. LGPD: consentimento abaixo."}
                {w.step === 2 &&
                  "M01 — Motor adaptativo: porte × regime × setor × UF filtram perguntas (LC 214/2025 art. 5º — previsibilidade). Ao concluir sem sessão na plataforma, o assistente **grava um rascunho na API** e segue para **OTP no e-mail**; com sessão iniciada, a gravação do diagnóstico é direta no tenant do JWT."}
                {w.step === 3 &&
                  "Uma pergunta por tela — Seguir / Voltar. Sem conta na plataforma: «Gerar diagnóstico» salva e segue para confirmar o e-mail e gravar na nuvem; com sessão iniciada, «Finalizar Diagnóstico» envia direto."}
              </CardDescription>
            </CardHeader>

            <CardContent
              ref={w.painelPerguntasRef}
              className={cn(
                w.step === 3
                  ? "flex flex-1 flex-col min-h-0 overflow-y-auto overscroll-contain px-4 pt-4 pb-2 md:pb-3 md:px-6"
                  : "px-6 pb-4 pt-6 sm:px-6",
              )}
            >
              <form
                className={cn(w.step === 3 ? "flex flex-col flex-1 min-h-full gap-0" : "space-y-6")}
                onSubmit={(e) => e.preventDefault()}
              >
                {w.step === 1 && (
                  <WizardStepIdentificacao register={w.register} control={w.control} errors={w.errors} />
                )}
                {w.step === 2 && (
                  <WizardStepPerfilEmpresa
                    catalogLoading={w.catalogLoading}
                    catalogError={w.catalogError}
                    register={w.register}
                    control={w.control}
                    errors={w.errors}
                    empresaPerfil={w.empresaPerfil}
                    selectPerfilVazio={w.selectPerfilVazio}
                    classSelectPerfil={w.classSelectPerfil}
                    cnaeAnchorRef={w.cnaeAnchorRef}
                    cnaeBuscaTexto={w.cnaeBuscaTexto}
                    setCnaeBuscaTexto={w.setCnaeBuscaTexto}
                    cnaeBuscaTextoRef={w.cnaeBuscaTextoRef}
                    cnaeListaAberta={w.cnaeListaAberta}
                    setCnaeListaAberta={w.setCnaeListaAberta}
                    cnaeBlurFecharTimerRef={w.cnaeBlurFecharTimerRef}
                    cnaeSugestoes={w.cnaeSugestoes}
                    cnaePopoverBox={w.cnaePopoverBox}
                    clearErrors={w.clearErrors}
                  />
                )}
                {w.step === 3 && (
                  <WizardStepQuestionario
                    apiError={w.apiError}
                    perguntas={w.perguntas}
                    indicePerguntaAtual={w.indicePerguntaAtual}
                    totalPerguntas={w.totalPerguntas}
                    normaTexto={w.normaTexto}
                    setNormaTexto={w.setNormaTexto}
                    normaFeedback={w.normaFeedback}
                    setNormaFeedback={w.setNormaFeedback}
                    normaCarregando={w.normaCarregando}
                    setNormaCarregando={w.setNormaCarregando}
                    register={w.register}
                    control={w.control}
                  />
                )}
              </form>
            </CardContent>

            {w.step !== 3 ? (
              <CardFooter className="flex w-full min-w-0 shrink-0 flex-wrap justify-between gap-3 border-t bg-muted/10 p-6 pb-[max(1.5rem,env(safe-area-inset-bottom,0px))] sm:pb-6">
                <WizardNavigationButtons {...navProps} larguraCheiaEmMobile={false} />
              </CardFooter>
            ) : null}
          </Card>
          {w.step === 3 ? (
            <div
              role="toolbar"
              aria-label="Navegação do questionário"
              className="flex w-full shrink-0 flex-col-reverse gap-3 border-t border-primary/10 bg-muted/50 px-4 py-4 pb-[max(1rem,env(safe-area-inset-bottom))] sm:flex-row sm:flex-wrap sm:items-center sm:justify-between md:px-6"
            >
              <WizardNavigationButtons {...navProps} larguraCheiaEmMobile />
            </div>
          ) : null}
        </div>
      </div>
    </>
  );
}
