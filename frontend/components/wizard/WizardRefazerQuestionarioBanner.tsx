"use client";

type Props = {
  razaoSocial: string;
};

/** Aviso no assistente — refazer questionário do mesmo ciclo (não cria novo diagnóstico). */
export function WizardRefazerQuestionarioBanner({ razaoSocial }: Props) {
  const razao = razaoSocial.trim();

  return (
    <div
      className="rounded-md border border-amber-500/40 bg-amber-500/10 px-3 py-3 text-sm leading-relaxed text-foreground"
      role="status"
    >
      <p>
        <strong className="font-semibold">Refazer questionário deste ciclo</strong>
        {razao ? (
          <>
            {" "}
            — <strong className="font-semibold">{razao}</strong>
          </>
        ) : null}
      </p>
      <p className="mt-2 text-muted-foreground text-xs leading-relaxed">
        As respostas foram carregadas da última versão gravada. Ao concluir, o score é recalculado no
        mesmo ciclo (evidência original preservada; retificação em cadeia). Não será criado um novo
        diagnóstico na lista.
      </p>
    </div>
  );
}
