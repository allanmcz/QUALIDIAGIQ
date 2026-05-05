"use client";

import { createPortal } from "react-dom";
import { Controller } from "react-hook-form";
import type { Control, FieldErrors, UseFormClearErrors, UseFormRegister } from "react-hook-form";
import type { MutableRefObject } from "react";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { SlotMensagemErroCampo } from "@/components/wizard/SlotMensagemErroCampo";
import type { CnaeSubclasseItem } from "@/lib/api/cnae";
import { getAccessToken } from "@/lib/api/config";
import {
  MENSAGEM_SELECT_PERFIL_EMPRESA,
  type DiagnosticoPayloadFormInput,
  UFS_BR,
} from "@/lib/schemas/wizard";
import { cn } from "@/lib/utils";

export type WizardStepPerfilEmpresaProps = {
  catalogLoading: boolean;
  catalogError: string | null;
  register: UseFormRegister<DiagnosticoPayloadFormInput>;
  control: Control<DiagnosticoPayloadFormInput>;
  errors: FieldErrors<DiagnosticoPayloadFormInput>;
  empresaPerfil: DiagnosticoPayloadFormInput["empresa"];
  selectPerfilVazio: (v: string | undefined) => boolean;
  classSelectPerfil: (erro: boolean, vazio: boolean) => string;
  cnaeAnchorRef: MutableRefObject<HTMLDivElement | null>;
  cnaeBuscaTexto: string;
  setCnaeBuscaTexto: (v: string) => void;
  cnaeBuscaTextoRef: MutableRefObject<string>;
  cnaeListaAberta: boolean;
  setCnaeListaAberta: (v: boolean) => void;
  cnaeBlurFecharTimerRef: MutableRefObject<ReturnType<typeof setTimeout> | null>;
  cnaeSugestoes: CnaeSubclasseItem[];
  cnaePopoverBox: { top: number; left: number; width: number } | null;
  clearErrors: UseFormClearErrors<DiagnosticoPayloadFormInput>;
};

export function WizardStepPerfilEmpresa({
  catalogLoading,
  catalogError,
  register,
  control,
  errors,
  empresaPerfil,
  selectPerfilVazio,
  classSelectPerfil,
  cnaeAnchorRef,
  cnaeBuscaTexto,
  setCnaeBuscaTexto,
  cnaeBuscaTextoRef,
  cnaeListaAberta,
  setCnaeListaAberta,
  cnaeBlurFecharTimerRef,
  cnaeSugestoes,
  cnaePopoverBox,
  clearErrors,
}: WizardStepPerfilEmpresaProps) {
  return (
    <div className="space-y-5 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <span className="sr-only" aria-live="polite">
        {catalogLoading ? "Carregando questionário adaptativo." : ""}
      </span>
      {!getAccessToken() && (
        <div className="rounded-md border border-border bg-muted/30 px-4 py-3 text-xs text-muted-foreground md:text-sm leading-relaxed">
          Sem login corporativo você pode concluir o assistente; na última pergunta,{" "}
          <span className="font-medium text-foreground">Gerar diagnóstico</span> guarda as respostas e abre a etapa
          seguinte: confirmação do e-mail (código) para gravar na nuvem ou login na plataforma para o painel consultor.
        </div>
      )}
      {catalogError && (
        <div className="rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
          {catalogError}
        </div>
      )}
      <div className="grid grid-cols-1 gap-x-6 gap-y-3 md:grid-cols-2 md:items-start">
        <div className="flex min-w-0 flex-col gap-2">
          <Label htmlFor="porte" className="text-foreground">
            Porte da empresa (faturamento anual) *
          </Label>
          <select
            id="porte"
            className={classSelectPerfil(!!errors.empresa?.porte, selectPerfilVazio(empresaPerfil.porte))}
            {...register("empresa.porte")}
          >
            <option value="" disabled>
              {MENSAGEM_SELECT_PERFIL_EMPRESA}
            </option>
            <option value="micro">Micro — faturamento anual até R$ 360 mil</option>
            <option value="pequeno">Pequeno — faturamento anual até R$ 4,8 milhões</option>
            <option value="medio">Médio — faturamento anual até R$ 500 milhões</option>
            <option value="grande">Grande — faturamento anual acima de R$ 500 milhões</option>
          </select>
          <SlotMensagemErroCampo>{errors.empresa?.porte ? errors.empresa.porte.message : null}</SlotMensagemErroCampo>
        </div>
        <div className="flex min-w-0 flex-col gap-2">
          <Label htmlFor="regime" className="text-foreground">
            Regime tributário *
          </Label>
          <select
            id="regime"
            className={classSelectPerfil(!!errors.empresa?.regime, selectPerfilVazio(empresaPerfil.regime))}
            {...register("empresa.regime")}
          >
            <option value="" disabled>
              {MENSAGEM_SELECT_PERFIL_EMPRESA}
            </option>
            <option value="simples_nacional">Simples Nacional</option>
            <option value="lucro_presumido">Lucro Presumido</option>
            <option value="lucro_real">Lucro Real</option>
            <option value="mei">MEI</option>
          </select>
          <SlotMensagemErroCampo>{errors.empresa?.regime ? errors.empresa.regime.message : null}</SlotMensagemErroCampo>
        </div>
      </div>
      <p className="-mt-1 text-xs text-muted-foreground leading-snug md:col-span-2">
        Porte: classificação por receita bruta dos últimos 12 meses (autodeclarada — não substitui enquadramento legal).
      </p>

      <div className="grid grid-cols-1 gap-x-6 gap-y-3 md:grid-cols-2 md:items-start">
        <div className="flex min-w-0 flex-col gap-2">
          <Label htmlFor="setor_macro" className="text-foreground">
            Setor macro *
          </Label>
          <select
            id="setor_macro"
            className={classSelectPerfil(
              !!errors.empresa?.setor_macro,
              selectPerfilVazio(empresaPerfil.setor_macro),
            )}
            {...register("empresa.setor_macro")}
          >
            <option value="" disabled>
              {MENSAGEM_SELECT_PERFIL_EMPRESA}
            </option>
            <option value="comercio">Comércio</option>
            <option value="industria">Indústria</option>
            <option value="servicos">Serviços</option>
            <option value="agro">Agro</option>
            <option value="consumo">Consumo</option>
          </select>
          <SlotMensagemErroCampo>
            {errors.empresa?.setor_macro ? errors.empresa.setor_macro.message : null}
          </SlotMensagemErroCampo>
        </div>
        <div className="flex min-w-0 flex-col gap-2">
          <Label htmlFor="uf" className="text-foreground">
            UF *
          </Label>
          <select
            id="uf"
            className={classSelectPerfil(!!errors.empresa?.uf, selectPerfilVazio(empresaPerfil.uf))}
            {...register("empresa.uf")}
          >
            <option value="" disabled>
              {MENSAGEM_SELECT_PERFIL_EMPRESA}
            </option>
            {UFS_BR.map((uf) => (
              <option key={uf} value={uf}>
                {uf}
              </option>
            ))}
          </select>
          <SlotMensagemErroCampo>{errors.empresa?.uf ? errors.empresa.uf.message : null}</SlotMensagemErroCampo>
        </div>
      </div>

      <div className="space-y-2 border-t border-border/60 pt-5">
        <Label htmlFor="cnae_principal">CNAE principal (7 dígitos) *</Label>
        <Controller
          name="empresa.cnae_principal"
          control={control}
          render={({ field, fieldState }) => (
            <div ref={cnaeAnchorRef} className="relative z-20 w-full min-w-0">
              <Input
                id="cnae_principal"
                placeholder="1234567 ou busque por texto (ex.: varejo)"
                autoComplete="off"
                aria-autocomplete="list"
                aria-expanded={cnaeListaAberta && cnaeSugestoes.length > 0}
                aria-controls="cnae-sugestoes-wizard-listbox"
                value={cnaeBuscaTexto}
                onChange={(e) => {
                  const v = e.target.value;
                  cnaeBuscaTextoRef.current = v;
                  setCnaeBuscaTexto(v);
                  const temLetras = /[a-zA-ZÀ-ÿ]/i.test(v);
                  const soDigitos = v.replace(/\D/g, "").slice(0, 7);
                  if (temLetras) {
                    field.onChange("");
                  } else {
                    field.onChange(soDigitos);
                  }
                }}
                onFocus={() => {
                  if (cnaeBlurFecharTimerRef.current != null) {
                    clearTimeout(cnaeBlurFecharTimerRef.current);
                    cnaeBlurFecharTimerRef.current = null;
                  }
                  setCnaeListaAberta(true);
                }}
                onBlur={() => {
                  field.onBlur();
                  const v = cnaeBuscaTextoRef.current;
                  const d = v.replace(/\D/g, "").slice(0, 7);
                  const temLetras = /[a-zA-ZÀ-ÿ]/i.test(v);
                  if (!temLetras && d.length === 7) {
                    field.onChange(d);
                    cnaeBuscaTextoRef.current = d;
                    setCnaeBuscaTexto(d);
                    clearErrors("empresa.cnae_principal");
                  } else if (temLetras) {
                    field.onChange("");
                  } else if (!temLetras && d.length > 0 && d.length < 7) {
                    field.onChange(d);
                    cnaeBuscaTextoRef.current = d;
                    setCnaeBuscaTexto(d);
                  } else if (!temLetras && d.length === 0) {
                    field.onChange("");
                    cnaeBuscaTextoRef.current = "";
                    setCnaeBuscaTexto("");
                  }
                  cnaeBlurFecharTimerRef.current = setTimeout(() => {
                    setCnaeListaAberta(false);
                  }, 200);
                }}
                className={fieldState.error ? "border-destructive" : ""}
              />
              {typeof document !== "undefined" &&
              cnaeListaAberta &&
              cnaeSugestoes.length > 0 &&
              cnaePopoverBox != null
                ? createPortal(
                    <ul
                      id="cnae-sugestoes-wizard-listbox"
                      role="listbox"
                      data-testid="cnae-sugestoes-lista"
                      style={{
                        position: "fixed",
                        top: cnaePopoverBox.top,
                        left: cnaePopoverBox.left,
                        width: cnaePopoverBox.width,
                        boxSizing: "border-box",
                      }}
                      className={cn(
                        "z-[300] max-h-[min(18rem,50vh)] overflow-y-auto overscroll-contain rounded-md border",
                        "border-border bg-popover p-0 text-popover-foreground shadow-lg",
                      )}
                    >
                      {cnaeSugestoes.map((s) => (
                        <li
                          key={s.subclasse_id}
                          role="presentation"
                          className="border-b border-border/40 last:border-b-0"
                        >
                          <button
                            type="button"
                            role="option"
                            aria-selected={false}
                            className={cn(
                              "flex w-full min-w-0 flex-col gap-0.5 px-3 py-2.5 text-left text-sm transition-colors",
                              "hover:bg-accent hover:text-accent-foreground focus-visible:bg-accent focus-visible:outline-none",
                            )}
                            onMouseDown={(e) => {
                              e.preventDefault();
                            }}
                            onClick={() => {
                              field.onChange(s.subclasse_id);
                              cnaeBuscaTextoRef.current = s.subclasse_id;
                              setCnaeBuscaTexto(s.subclasse_id);
                              clearErrors("empresa.cnae_principal");
                              setCnaeListaAberta(false);
                            }}
                          >
                            <span className="shrink-0 font-mono text-xs font-semibold tabular-nums text-foreground">
                              {s.subclasse_id}
                            </span>
                            <span className="min-w-0 whitespace-normal break-words text-xs leading-snug text-muted-foreground [overflow-wrap:anywhere]">
                              {s.descricao}
                            </span>
                          </button>
                        </li>
                      ))}
                    </ul>,
                    document.body,
                  )
                : null}
            </div>
          )}
        />
        <p className="text-xs text-muted-foreground leading-snug">
          Digite pelo menos 2 caracteres (início do código de 7 dígitos ou parte da descrição da atividade). As sugestões
          aparecem <strong className="font-medium text-foreground">abaixo do campo</strong>, com rolagem e texto
          completo. Tabela oficial{" "}
          <abbr title="Classificação Nacional de Atividades Econômicas">CNAE</abbr> 2.3 (CONCLA/IBGE).
        </p>
        {errors.empresa?.cnae_principal && (
          <p className="text-sm text-destructive">{errors.empresa.cnae_principal.message}</p>
        )}
      </div>
    </div>
  );
}
