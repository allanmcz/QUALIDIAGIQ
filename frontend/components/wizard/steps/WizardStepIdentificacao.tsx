"use client";

import Link from "next/link";
import { Controller } from "react-hook-form";
import type { Control, FieldErrors, UseFormRegister } from "react-hook-form";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { DiagnosticoPayloadFormInput } from "@/lib/schemas/wizard";
import { cn } from "@/lib/utils";
import { mascaraTelefoneBR } from "@/lib/utils/mascaraTelefoneBr";

export type WizardStepIdentificacaoProps = {
  register: UseFormRegister<DiagnosticoPayloadFormInput>;
  control: Control<DiagnosticoPayloadFormInput>;
  errors: FieldErrors<DiagnosticoPayloadFormInput>;
  hasToken: boolean;
  consultaCnpjLoading: boolean;
  consultaCnpjFeedback: string | null;
  forceRefreshConsultaCnpj: boolean;
  setForceRefreshConsultaCnpj: (v: boolean) => void;
  onConsultarCnpjPublico: () => void;
};

export function WizardStepIdentificacao({
  register,
  control,
  errors,
  hasToken,
  consultaCnpjLoading,
  consultaCnpjFeedback,
  forceRefreshConsultaCnpj,
  setForceRefreshConsultaCnpj,
  onConsultarCnpjPublico,
}: WizardStepIdentificacaoProps) {
  return (
    <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div>
        <h3 className="text-sm font-semibold text-foreground tracking-tight">Cadastro da empresa</h3>
        <p className="text-xs text-muted-foreground mt-1">
          {hasToken ? (
            <>
              Com <strong className="font-medium text-foreground">sessão na plataforma</strong>, o{" "}
              <strong className="font-medium text-foreground">CNPJ é obrigatório</strong> (14 dígitos, DV válido)
              para histórico por empresa no painel. Pode pré-preencher dados públicos antes de seguir.
            </>
          ) : (
            <>
              Sem sessão, o CNPJ é <strong className="font-medium text-foreground">opcional</strong> neste passo; se
              preencher, use 14 dígitos com DV válidos. O fluxo segue para confirmar por e-mail (OTP) e gravar no
              ambiente self-service.
            </>
          )}
        </p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="space-y-2 md:col-span-2">
          <Label htmlFor="cnpj">{hasToken ? "CNPJ *" : "CNPJ (opcional)"}</Label>
          <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:gap-3">
            <Input
              id="cnpj"
              placeholder="00.000.000/0000-00"
              inputMode="numeric"
              autoComplete="organization"
              {...register("empresa.cnpj")}
              className={cn("flex-1", errors.empresa?.cnpj ? "border-destructive" : "")}
            />
            <div className="flex flex-col gap-2 shrink-0 w-full sm:w-auto">
              <Button
                type="button"
                variant="secondary"
                className="w-full sm:w-auto whitespace-nowrap"
                disabled={consultaCnpjLoading || !hasToken}
                title={
                  !hasToken
                    ? "Disponível com sessão iniciada na plataforma (Bearer JWT)."
                    : "Consulta dados públicos (BrasilAPI; reserva só em falha de rede)."
                }
                onClick={() => void onConsultarCnpjPublico()}
              >
                {consultaCnpjLoading ? "Consultando…" : "Buscar dados públicos"}
              </Button>
              {hasToken ? (
                <label className="flex items-start gap-2 text-xs text-muted-foreground cursor-pointer select-none leading-snug px-0.5">
                  <input
                    type="checkbox"
                    className="mt-0.5 h-3.5 w-3.5 shrink-0 rounded border-input"
                    checked={forceRefreshConsultaCnpj}
                    onChange={(e) => setForceRefreshConsultaCnpj(e.target.checked)}
                  />
                  <span>Ignorar cache nesta consulta — nova chamada às fontes públicas.</span>
                </label>
              ) : null}
            </div>
          </div>
          {errors.empresa?.cnpj && <p className="text-sm text-destructive">{errors.empresa.cnpj.message}</p>}
          {consultaCnpjFeedback ? (
            <p
              className={cn(
                "text-xs leading-relaxed rounded-md border px-2 py-2",
                consultaCnpjFeedback.toLowerCase().includes("atualizado") ||
                  consultaCnpjFeedback.toLowerCase().includes("campos")
                  ? "border-primary/25 bg-primary/5 text-foreground"
                  : "border-destructive/30 bg-destructive/5 text-destructive",
              )}
              role="status"
            >
              {consultaCnpjFeedback}
            </p>
          ) : null}
        </div>
        <div className="space-y-2 md:col-span-2">
          <Label htmlFor="razao_social">Razão Social *</Label>
          <Input
            id="razao_social"
            placeholder="Informe a razão social"
            {...register("empresa.razao_social")}
            className={errors.empresa?.razao_social ? "border-destructive" : ""}
          />
          {errors.empresa?.razao_social && (
            <p className="text-sm text-destructive">{errors.empresa.razao_social.message}</p>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t">
        <div className="space-y-2">
          <Label htmlFor="nome">Seu Nome *</Label>
          <Input
            id="nome"
            placeholder="Informe seu nome completo"
            {...register("respondente.nome")}
            className={errors.respondente?.nome ? "border-destructive" : ""}
          />
          {errors.respondente?.nome && <p className="text-sm text-destructive">{errors.respondente.nome.message}</p>}
        </div>
        <div className="space-y-2">
          <Label htmlFor="email">E-mail Profissional *</Label>
          <Input
            id="email"
            type="email"
            placeholder="nome@dominio.com.br"
            autoComplete="email"
            {...register("respondente.email")}
            className={errors.respondente?.email ? "border-destructive" : ""}
          />
          {errors.respondente?.email && (
            <p className="text-sm text-destructive">{errors.respondente.email.message}</p>
          )}
        </div>
      </div>

      <div className="space-y-2 max-w-md">
        <Label htmlFor="telefone">Telefone (opcional)</Label>
        <Controller
          name="respondente.telefone"
          control={control}
          render={({ field }) => (
            <Input
              id="telefone"
              type="tel"
              inputMode="numeric"
              autoComplete="tel-national"
              placeholder="(11) 98765-4321"
              maxLength={15}
              aria-describedby="hint-telefone"
              value={field.value ?? ""}
              onBlur={field.onBlur}
              onChange={(e) => field.onChange(mascaraTelefoneBR(e.target.value))}
            />
          )}
        />
        <p id="hint-telefone" className="text-xs text-muted-foreground">
          M09 — Apenas DDD e número (sem +55). No relatório PDF (WeasyPrint), o bloco de captação de lead mostra apenas
          e-mail e telefone.
        </p>
        <div className="space-y-2 max-w-md pt-2">
          <Label htmlFor="locale_relatorio">Idioma do relatório PDF</Label>
          <select
            id="locale_relatorio"
            className={cn(
              "flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm",
              "ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
            )}
            {...register("locale_relatorio")}
          >
            <option value="pt-BR">Português (Brasil)</option>
            <option value="en">English (labels; partial PT narrative)</option>
          </select>
        </div>
        {errors.respondente?.telefone != null &&
          typeof errors.respondente.telefone === "object" &&
          "message" in errors.respondente.telefone && (
            <p className="text-sm text-destructive">{errors.respondente.telefone.message as string}</p>
          )}
      </div>

      <div className="rounded-md border p-4 space-y-2 bg-muted/20">
        <div className="flex items-start gap-3">
          <Controller
            name="aceite_termos_privacidade"
            control={control}
            render={({ field }) => (
              <input
                type="checkbox"
                id="lgpd"
                className="mt-1 h-4 w-4"
                checked={field.value}
                onChange={(e) => field.onChange(e.target.checked)}
              />
            )}
          />
          <Label
            htmlFor="lgpd"
            className="block w-full min-w-0 font-normal text-sm leading-relaxed cursor-pointer text-left"
          >
            Declaro que li e aceito o tratamento dos dados informados para elaboração do diagnóstico, nos termos da LGPD
            (Lei 13.709/2018). Consulte a{" "}
            <Link href="/privacidade" className="text-primary underline underline-offset-2 hover:text-primary/90 inline">
              política de privacidade (QDI)
            </Link>
            .
          </Label>
        </div>
        {errors.aceite_termos_privacidade && (
          <p className="text-sm text-destructive">{errors.aceite_termos_privacidade.message}</p>
        )}
      </div>
      <p className="text-center text-sm md:text-base text-muted-foreground leading-relaxed pt-3 border-t border-border/60">
        Em <strong className="text-foreground font-semibold">cerca de 15 minutos</strong>, identifique lacunas frente à
        Reforma Tributária do Consumo (EC 132/2023, LC 214/2025) e receba um plano de ação objetivo para sua empresa.
      </p>
    </div>
  );
}
