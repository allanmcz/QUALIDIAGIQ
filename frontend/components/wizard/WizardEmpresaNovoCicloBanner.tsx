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
        Verificando histórico desta empresa no painel…
      </p>
    );
  }

  const razao = razaoSocial.trim() || resumo?.razaoSocialMaisRecente?.trim() || "";

  if (resumo != null && resumo.totalCiclos > 0) {
    const plural = resumo.totalCiclos === 1 ? "diagnóstico anterior" : "diagnósticos anteriores";
    return (
      <div
        className="rounded-md border border-primary/35 bg-primary/5 px-3 py-3 text-sm leading-relaxed text-foreground"
        role="status"
      >
        <p>
          <strong className="font-semibold">Empresa já cadastrada no painel.</strong>{" "}
          {resumo.totalCiclos} {plural}
          {razao ? (
            <>
              {" "}
              para <strong className="font-semibold">{razao}</strong>
            </>
          ) : null}
          .
        </p>
        <p className="mt-2 text-muted-foreground text-xs">
          Este assistente registrará o{" "}
          <strong className="text-foreground font-medium">
            ciclo nº {resumo.proximoNumeroInternoEstimado}
          </strong>{" "}
          (novo diagnóstico na mesma PJ — não é um novo cadastro de empresa).
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
        <strong className="font-semibold text-foreground">Novo ciclo de diagnóstico</strong>
        {razao ? (
          <>
            {" "}
            para <strong className="font-semibold">{razao}</strong>
          </>
        ) : null}
        . Os dados abaixo referem-se à mesma empresa do painel; ao concluir, será criado um novo ciclo
        numerado automaticamente.
      </div>
    );
  }

  return null;
}
