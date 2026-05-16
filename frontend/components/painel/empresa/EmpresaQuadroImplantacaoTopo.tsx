"use client";

import { EmpresaImplantacaoResumoDepartamentosCard } from "@/components/painel/empresa/EmpresaImplantacaoResumoDepartamentosCard";
import { QuadroImplantacaoGrid } from "@/components/painel/empresa/QuadroImplantacaoGrid";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
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
};

/**
 * Quadros 3 (gaps) + 4 (plano de implantação) — bloco único por CNPJ, abaixo da listagem de ciclos.
 */
export function EmpresaQuadroImplantacaoTopo({
  listaPainel,
  detalhesPorId,
  carregando = false,
  erro = null,
  onDataAtualizado,
}: Props) {
  if (!listaPainel?.length) return null;

  const quadroDetalhe = escolherDetalheQuadroEmpresa(listaPainel, detalhesPorId);
  const temLinhas = quadroDetalhe ? linhasQuadroGrid(quadroDetalhe.checklist).length > 0 : false;

  return (
    <Card className="mb-10" id="empresa-implantacao-bloco">
      <CardHeader>
        <CardTitle className="text-lg" id="empresa-implantacao-bloco-titulo">
          Implantação da empresa
        </CardTitle>
        <CardDescription className="max-w-3xl">
          <strong className="font-medium text-foreground">Um plano por CNPJ</strong> (ciclo de referência /
          baseline). O ranking detalhado de lacunas (M05) abre ao{" "}
          <strong className="font-medium text-foreground">Expandir</strong> cada linha na listagem acima.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-10">
        {carregando && !quadroDetalhe ? (
          <p className="text-sm text-muted-foreground" role="status" aria-live="polite">
            A carregar gaps e plano de implantação…
          </p>
        ) : null}

        {erro && !quadroDetalhe ? (
          <p className="text-sm text-destructive border border-destructive/30 rounded-md p-3" role="alert">
            {erro}
          </p>
        ) : null}

        {quadroDetalhe ? (
          <>
            <section className="space-y-4" aria-labelledby="empresa-quadro-gaps-titulo">
              <div>
                <h3
                  id="empresa-quadro-gaps-titulo"
                  className="text-base font-semibold tracking-tight scroll-mt-24"
                >
                  Gaps — consolidação por frente
                </h3>
                <p className="text-sm text-muted-foreground mt-1 max-w-3xl">
                  Resumo das lacunas do score materializado no quadro (M07). Pendente vs. finalizada conforme
                  prazo meta e comentários do consultor.
                </p>
              </div>
              <div id="empresa-quadro-gaps">
                <EmpresaImplantacaoResumoDepartamentosCard data={quadroDetalhe} />
              </div>
            </section>

            <section className="space-y-4" aria-labelledby="empresa-quadro-plano-titulo">
              <div>
                <h3
                  id="empresa-quadro-plano-titulo"
                  className="text-base font-semibold tracking-tight scroll-mt-24"
                >
                  Plano de implantação
                </h3>
                <p className="text-sm text-muted-foreground mt-1 max-w-3xl">
                  Grelha operacional: ações, responsáveis, prazos meta e comentários (único quadro editável por
                  empresa).
                </p>
              </div>
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
                  O ciclo de referência ainda não tem linhas no checklist — confirme que o diagnóstico baseline
                  está finalizado e que o plano M07/M08 foi materializado na API.
                </p>
              ) : null}
            </section>
          </>
        ) : !carregando && !erro ? (
          <p className="text-sm text-muted-foreground border rounded-md p-4 bg-muted/20" role="status">
            Aguarde a listagem de diagnósticos e o detalhe do ciclo de referência para exibir gaps e plano.
          </p>
        ) : null}
      </CardContent>
    </Card>
  );
}
