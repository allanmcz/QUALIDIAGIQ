"use client";

import { EmpresaImplantacaoResumoDepartamentosCard } from "@/components/painel/empresa/EmpresaImplantacaoResumoDepartamentosCard";
import { QuadroImplantacaoGrid } from "@/components/painel/empresa/QuadroImplantacaoGrid";
import type { DiagnosticoResumoApi } from "@/lib/api/lista_diagnosticos";
import {
  escolherDetalheQuadroEmpresa,
  quadroImplantacaoEditavel,
} from "@/lib/painel/diagnostico_empresa_ordem";
import { linhasQuadroGrid } from "@/lib/painel/quadro_implantacao_utils";
import type { DiagnosticoDetalheApi } from "@/types/diagnostico_detalhe";

type Props = {
  listaPainel: DiagnosticoResumoApi[] | null;
  detalhesPorId: Record<string, DiagnosticoDetalheApi | undefined>;
  carregando?: boolean;
  erro?: string | null;
  onDataAtualizado?: (d: DiagnosticoDetalheApi) => void;
  /** Texto introdutório extra (ex.: ficha do diagnóstico). */
  mostrarIntro?: boolean;
};

/**
 * Secção «Quadro de implantação da empresa» — grelha única por CNPJ (topo da vista empresa ou card na ficha).
 */
export function EmpresaQuadroImplantacaoTopo({
  listaPainel,
  detalhesPorId,
  carregando = false,
  erro = null,
  onDataAtualizado,
  mostrarIntro = true,
}: Props) {
  if (!listaPainel?.length) return null;

  const quadroDetalhe = escolherDetalheQuadroEmpresa(listaPainel, detalhesPorId);
  const temLinhas = quadroDetalhe ? linhasQuadroGrid(quadroDetalhe.checklist).length > 0 : false;

  return (
    <section className="space-y-6" aria-labelledby="empresa-quadro-implantacao-titulo">
      {mostrarIntro ? (
        <div>
          <h2 id="empresa-quadro-implantacao-titulo" className="text-lg font-semibold tracking-tight">
            Quadro de implantação da empresa
          </h2>
          <p className="text-sm text-muted-foreground mt-1 max-w-3xl">
            <strong className="font-medium text-foreground">Um quadro por empresa</strong> para o mesmo CNPJ:
            prazos meta e notas do consultor aplicam-se à implantação global. Na lista de ciclos abaixo,{" "}
            <strong className="font-medium text-foreground">Expandir</strong> mostra M05, matriz e M12 só
            daquele diagnóstico.
          </p>
        </div>
      ) : null}

      {carregando && !quadroDetalhe ? (
        <p className="text-sm text-muted-foreground" role="status" aria-live="polite">
          A carregar o plano de implantação da empresa…
        </p>
      ) : null}

      {erro && !quadroDetalhe ? (
        <p className="text-sm text-destructive border border-destructive/30 rounded-md p-3" role="alert">
          {erro}
        </p>
      ) : null}

      {quadroDetalhe ? (
        <>
          <EmpresaImplantacaoResumoDepartamentosCard data={quadroDetalhe} />
          <QuadroImplantacaoGrid
            diagnosticoId={quadroDetalhe.id}
            data={quadroDetalhe}
            editavel={quadroImplantacaoEditavel(quadroDetalhe.id, listaPainel, quadroDetalhe.status)}
            avisoSomenteLeitura={
              !quadroImplantacaoEditavel(quadroDetalhe.id, listaPainel, quadroDetalhe.status) &&
              quadroDetalhe.status === "finalizado"
                ? "Quadro da empresa em consulta: a edição fica concentrada no ciclo de referência da empresa."
                : undefined
            }
            onDataAtualizado={onDataAtualizado}
            id="empresa-quadro-implantacao-principal"
          />
          {!temLinhas ? (
            <p className="text-xs text-muted-foreground">
              O ciclo de referência ainda não tem linhas no checklist — confirme que o diagnóstico baseline está
              finalizado e que o plano M07/M08 foi materializado na API.
            </p>
          ) : null}
        </>
      ) : !carregando && !erro ? (
        <p className="text-sm text-muted-foreground border rounded-md p-4 bg-muted/20" role="status">
          Aguarde a lista de diagnósticos e o detalhe do ciclo de referência para exibir a grelha.
        </p>
      ) : null}
    </section>
  );
}
