"use client";

import { Controller } from "react-hook-form";
import type { Control, UseFormRegister } from "react-hook-form";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { PerguntaCatalogo } from "@/lib/api/questionario";
import type { DiagnosticoPayloadFormInput } from "@/lib/schemas/wizard";
import { rotulosEscalaParaPergunta } from "@/lib/wizard/escalaLabels";
import { montarRotulosMultiplaEscolha } from "@/lib/wizard/multiplaLabels";
import { normalizarTipoPerguntaWizard } from "@/lib/wizard/perguntaTipo";

export type WizardPerguntaInputProps = {
  pergunta: PerguntaCatalogo;
  index: number;
  register: UseFormRegister<DiagnosticoPayloadFormInput>;
  control: Control<DiagnosticoPayloadFormInput>;
};

export function WizardPerguntaInput({ pergunta: p, index, register, control }: WizardPerguntaInputProps) {
  const base = `respostas.${index}.valor` as const;
  const rowClass =
    "flex items-center space-x-3 cursor-pointer p-3 rounded border bg-background hover:bg-muted/50 transition-colors";
  const t = normalizarTipoPerguntaWizard(p.tipo);

  if (t === "escala_1_5") {
    const rotulos = rotulosEscalaParaPergunta(p.rotulos_escala);
    return (
      <div className="flex flex-col gap-2 pt-2" role="group" aria-label="Resposta em escala de 1 a 5">
        {[1, 2, 3, 4, 5].map((n) => (
          <Label
            key={n}
            className={`${rowClass} w-full flex-wrap items-start gap-3 py-3 sm:items-center`}
          >
            <div className="flex shrink-0 items-center gap-2">
              <input
                type="radio"
                value={String(n)}
                className="h-4 w-4 text-primary focus:ring-primary"
                {...register(base)}
              />
              <span className="inline-flex min-w-[1.5rem] justify-center rounded-md bg-muted px-2 py-0.5 text-sm font-semibold tabular-nums text-foreground">
                {n}
              </span>
            </div>
            <span className="min-w-0 flex-1 text-sm font-normal leading-snug text-foreground">
              {rotulos[n - 1]}
            </span>
          </Label>
        ))}
      </div>
    );
  }

  if (t === "binaria") {
    const opts = [
      { v: "sim", l: "Sim" },
      { v: "nao", l: "Não" },
    ];
    return (
      <div className="flex flex-col space-y-2 pt-2">
        {opts.map((o) => (
          <Label key={o.v} className={rowClass}>
            <input type="radio" value={o.v} className="w-4 h-4 text-primary focus:ring-primary" {...register(base)} />
            <span className="font-normal text-sm">{o.l}</span>
          </Label>
        ))}
      </div>
    );
  }

  if (t === "numerica") {
    return (
      <Input
        type="number"
        min={0}
        max={100}
        step={1}
        placeholder="Ex.: 72"
        className="max-w-xs mt-2"
        {...register(base)}
      />
    );
  }

  if (t === "multipla_escolha" || t === "checklist") {
    const total = p.multipla_total ?? 0;
    const { labels: rowLabels, avisoRotulos } = montarRotulosMultiplaEscolha(total, p.opcoes ?? [], p.codigo);
    if (total < 1) {
      return (
        <p className="text-sm text-destructive pt-2">
          Catálogo incompleto: multipla_total ausente ou inválido para {p.codigo}.
        </p>
      );
    }
    return (
      <>
        {avisoRotulos ? (
          <p
            className="text-sm text-amber-800 dark:text-amber-400 mt-2 rounded-md border border-amber-500/35 bg-amber-500/10 px-3 py-2"
            role="status"
          >
            {avisoRotulos}
          </p>
        ) : null}
        <Controller
          name={base}
          control={control}
          render={({ field }) => {
            const selected = Array.isArray(field.value) ? field.value : [];
            return (
              <div className="flex flex-col space-y-2 pt-2">
                {rowLabels.map((label, i) => {
                  const key = `opt_${i + 1}`;
                  const checked = selected.includes(key);
                  return (
                    <Label key={key} className={rowClass}>
                      <input
                        type="checkbox"
                        className="w-4 h-4 rounded border-input text-primary"
                        checked={checked}
                        onChange={(e) => {
                          const cur = Array.isArray(field.value) ? [...field.value] : [];
                          if (e.target.checked) field.onChange([...cur, key]);
                          else field.onChange(cur.filter((x) => x !== key));
                        }}
                      />
                      <span className="font-normal text-sm">{label}</span>
                    </Label>
                  );
                })}
              </div>
            );
          }}
        />
      </>
    );
  }

  const opts = [
    { v: "sim", l: "Sim" },
    { v: "parcialmente", l: "Parcialmente" },
    { v: "nao", l: "Não" },
    { v: "nao_se_aplica", l: "Não se aplica ao meu negócio" },
  ];
  return (
    <div className="flex flex-col space-y-2 pt-2">
      {opts.map((o) => (
        <Label key={o.v} className={rowClass}>
          <input type="radio" value={o.v} className="w-4 h-4 text-primary focus:ring-primary" {...register(base)} />
          <span className="font-normal text-sm">{o.l}</span>
        </Label>
      ))}
    </div>
  );
}
