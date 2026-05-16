"use client";

import type { ResumoCiclosEmpresaPainel } from "@/lib/wizard/empresa_painel_ciclos";

type Props = {
  carregando: boolean;
  resumo: ResumoCiclosEmpresaPainel | null;
  razaoSocial: string;
  /** Veio do painel com `modo=novo_ciclo` (mesmo sem histórico ainda). */
  modoNovoCicloExplicito: boolean;
};

/**
 * Aviso no passo 1/2: PJ já tem histórico no tenant ou primeiro ciclo explícito do painel.
 */
export function WizardEmpresaNovoCicloBanner({
  carregando,
  resumo,
  razaoSocial,
  modoNovoCicloExplicito,
}: Props) {
  if (!modoNovoCicloExplicito && (resumo == null || resumo.totalCiclos === 0)) {
    return null;
  }

  if (carregando) {
    return (
      <p className="text-xs text-muted-foreground" role="status" aria-live="polite">
        Recuperando o histórico desta empresa na plataforma…
      </p>
    );
  }

  const razao = razaoSocial.trim() || resumo?.razaoSocialMaisRecente?.trim() || "";

  if (resumo != null && resumo.totalCiclos > 0) {
    const pluralDiag =
      resumo.totalCiclos === 1 ? "1 diagnóstico já realizado" : `${resumo.totalCiclos} diagnósticos já realizados`;
    const proximo = resumo.proximoNumeroInternoEstimado;
    return (
      <div
        className="rounded-md border border-primary/35 bg-primary/5 px-3 py-3 text-sm leading-relaxed text-foreground"
        role="status"
      >
        <p>
          <strong className="font-semibold">Boa notícia: esta empresa já faz parte da sua base.</strong>
          {razao ? (
            <>
              {" "}
              Para <strong className="font-semibold">{razao}</strong>, encontramos{" "}
              <strong className="font-semibold">{pluralDiag}</strong> na plataforma.
            </>
          ) : (
            <>
              {" "}
              Encontramos <strong className="font-semibold">{pluralDiag}</strong> na plataforma.
            </>
          )}
        </p>
        <p className="mt-2 text-muted-foreground text-xs leading-relaxed">
          Agora vamos registrar o{" "}
          <strong className="text-foreground font-medium">{proximo}º ciclo de maturidade</strong> — uma
          nova leitura da prontidão para a Reforma do Consumo, com histórico preservado e comparável ao
          ciclo anterior. Não é um novo cadastro: é a evolução do mesmo acompanhamento.
        </p>
      </div>
    );
  }

  if (modoNovoCicloExplicito) {
    return (
      <div
        className="rounded-md border border-border/80 bg-muted/30 px-3 py-3 text-sm leading-relaxed"
        role="status"
      >
        <p className="text-foreground">
          <strong className="font-semibold">Vamos abrir um novo ciclo de maturidade</strong>
          {razao ? (
            <>
              {" "}
              para <strong className="font-semibold">{razao}</strong>
            </>
          ) : null}
          .
        </p>
        <p className="mt-2 text-muted-foreground text-xs leading-relaxed">
          Confirme os dados abaixo e avance: ao concluir, o resultado entra no histórico da empresa na
          plataforma, com numeração automática e comparável aos ciclos anteriores.
        </p>
      </div>
    );
  }

  return null;
}
