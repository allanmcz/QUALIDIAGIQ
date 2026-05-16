import { describe, expect, it } from "vitest";

import type { DiagnosticoResumoApi } from "@/lib/api/lista_diagnosticos";
import {
  escolherDetalheQuadroEmpresa,
  idDiagnosticoBaselineQuadroEmpresa,
} from "@/lib/painel/diagnostico_empresa_ordem";
import type { DiagnosticoDetalheApi } from "@/types/diagnostico_detalhe";

const lista: DiagnosticoResumoApi[] = [
  {
    id: "aaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
    empresa_razao_social: "Antiga",
    status: "finalizado",
    plano: "gratuito",
    score_geral: 40,
    criado_em: "2026-01-01T10:00:00Z",
    finalizado_em: "2026-01-01T11:00:00Z",
    relatorio_pdf_url: null,
  },
  {
    id: "bbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
    empresa_razao_social: "Nova",
    status: "finalizado",
    plano: "gratuito",
    score_geral: 55,
    criado_em: "2026-05-01T10:00:00Z",
    finalizado_em: "2026-05-01T11:00:00Z",
    relatorio_pdf_url: null,
  },
];

function detalheComChecklist(id: string): DiagnosticoDetalheApi {
  return {
    id,
    empresa_razao_social: "X",
    empresa_cnpj: "12345678000195",
    status: "finalizado",
    plano: "gratuito",
    versao_otimista: 1,
    relatorio_pdf_url: null,
    checklist: [
      {
        nome: "Frente 1",
        acoes: [
          {
            descricao: "Ação teste",
            responsavel: "QA",
            prazo: "—",
            criticidade: "Média",
          },
        ],
      },
    ],
    checklist_m12_autoconf: null,
    cronograma: [],
    matriz_impacto: [],
    score: {
      score_geral: { valor: 50 },
      score_por_dimensao: { fiscal: { valor: 50, peso_total_aplicado: 1 } },
    },
  };
}

describe("diagnostico_empresa_ordem", () => {
  it("baseline do quadro é o ciclo finalizado mais antigo", () => {
    expect(idDiagnosticoBaselineQuadroEmpresa(lista)).toBe("aaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa");
  });

  it("escolhe detalhe com checklist mesmo se baseline ainda vazio", () => {
    const detalhes = {
      "aaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa": { ...detalheComChecklist("aaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"), checklist: null },
      "bbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb": detalheComChecklist("bbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"),
    };
    const escolhido = escolherDetalheQuadroEmpresa(lista, detalhes);
    expect(escolhido?.id).toBe("bbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb");
  });
});
