import type { Page } from "@playwright/test";
import { expect, test } from "@playwright/test";

import { installMockBffPainelLogin } from "./helpers/mock_bff_painel_auth";
import { painelInterceptarUrlApiDiagnosticos } from "./helpers/painel_api_diagnosticos_url";

/** Smoke handoff P3 — grelha empresa + expandir (API mockada; sem backend real). */
const DIAG_ID = "22222222-2222-4222-a222-222222222222";
const CNPJ14 = "12345678000195";
/** Primeira linha do plano — alinhada ao card Kanban mockado. */
const PLANO_ACAO_ID_1 = "33333333-3333-4333-a333-333333333331";

const narrativaLlm = {
  text: "Priorize a dimensão fiscal (42/100) antes da transição CBS/IBS (LC 214/2025).",
  provider: "fake",
  model: "fake-llm",
  policy_version: "2026-05-15-v1",
  input_tokens: 1,
  output_tokens: 2,
  estimated_cost_usd: 0,
  latency_ms: 10,
  blocked_by_guardrail: false,
  guardrail_reason: null,
  guardrail_status: "ok",
  gerado_em: "2026-05-15T12:00:00+00:00",
  trace_id: "e2e-trace-empresa-explic",
};

const narrativaAnterior = {
  ...narrativaLlm,
  text: "Versão anterior da narrativa fiscal.",
  gerado_em: "2026-05-14T10:00:00+00:00",
  trace_id: "e2e-trace-empresa-explic-ant",
};

function buildAbnt10Acoes() {
  return Array.from({ length: 10 }, (_, i) => ({
    descricao: `Controle ABNT M12 #${i + 1} (E2E)`,
    responsavel: "QA",
    prazo: "—",
    criticidade: "Média",
    prioridade: i + 1,
    plano_acao_id:
      i === 0
        ? PLANO_ACAO_ID_1
        : `33333333-3333-4333-b333-${String(i).padStart(12, "0")}`,
  }));
}

function buildKanbanBoardMock() {
  const acoes = buildAbnt10Acoes();
  return {
    diagnostico_id: DIAG_ID,
    cards: acoes.map((acao, ordem) => ({
      plano_acao_id: acao.plano_acao_id,
      diagnostico_id: DIAG_ID,
      frente_indice: 0,
      frente_nome: "ABNT NBR 17301 — 10 controlos M12",
      acao_indice: ordem,
      texto_acao: acao.descricao,
      responsavel_sugerido: acao.responsavel,
      prioridade_motor: acao.prioridade,
      criticidade: acao.criticidade,
      chave_quadro_legado: `f0_a${ordem}`,
      status_execucao: ordem === 0 ? "em_andamento" : "pendente",
      ordem_kanban: ordem,
      arquivado: false,
      comentarios_total: 0,
      subtarefas_total: 0,
    })),
  };
}

const listaItem = {
  id: DIAG_ID,
  empresa_razao_social: "Empresa E2E Painel Empresa",
  empresa_cnpj: CNPJ14,
  status: "finalizado",
  plano: "gratuito",
  score_geral: 52,
  criado_em: "2026-05-11T10:00:00Z",
  finalizado_em: "2026-05-11T10:30:00Z",
  relatorio_pdf_url: null,
  versao_otimista: 1,
  painel_estado_ciclo: "realizado",
};

type InstallMocksOpts = {
  explicacaoInicial?: typeof narrativaLlm | null;
  perfilConta?: "gratuito" | "avancado";
};

function detalheBody(explicacao: typeof narrativaLlm | null) {
  return {
    id: DIAG_ID,
    empresa_razao_social: listaItem.empresa_razao_social,
    empresa_cnpj: CNPJ14,
    status: "finalizado",
    plano: "gratuito",
    versao_otimista: 1,
    relatorio_pdf_url: null,
    checklist_m12_autoconf: null,
    quadro_implantacao_anotacoes: null,
    matriz_impacto: [],
    cronograma: [],
    score: {
      score_geral: { valor: 52 },
      score_por_dimensao: {
        fiscal: { valor: 42, peso_total_aplicado: 1.5 },
        tecnologica: { valor: 62, peso_total_aplicado: 1.3 },
      },
    },
    explicacao_score_llm: explicacao,
    checklist: [
      {
        nome: "ABNT NBR 17301 — 10 controlos M12",
        acoes: buildAbnt10Acoes(),
      },
    ],
  };
}

/**
 * Mocks partilhados: login, lista/detalhe diagnósticos, retificações (lista vazia),
 * solicitações LGPD (lista vazia — card «Nenhuma solicitação…»).
 */
async function installPainelEmpresaApiMocks(
  page: Page,
  opts: InstallMocksOpts = {},
): Promise<void> {
  const explicacaoAtual = opts.explicacaoInicial ?? null;

  await installMockBffPainelLogin(page, {
    tokenParaUpstream: "e2e-empresa-token",
    nome: "Consultor QA",
    perfil_conta: opts.perfilConta ?? "gratuito",
    limparLocalStoragePainelAntesDeCadaDocumento: true,
  });

  await page.route("**/privacidade/solicitacoes**", async (route) => {
    if (route.request().method() !== "GET") {
      await route.continue();
      return;
    }
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify([]),
    });
  });

  await page.route(painelInterceptarUrlApiDiagnosticos, async (route) => {
    const method = route.request().method();
    const pathname = new URL(route.request().url()).pathname.replace(/\/$/, "");
    // Não interceptar UI `/dashboard/diagnosticos/...` — glob `diagnosticos` apanha também o fetch RSC do Next.
    if (pathname.includes("/dashboard/diagnosticos")) {
      await route.continue();
      return;
    }
    const parts = pathname.split("/").filter(Boolean);
    const di = parts.lastIndexOf("diagnosticos");
    if (di === -1) {
      await route.continue();
      return;
    }
    const rest = parts.slice(di + 1);

    if (
      rest.length >= 3 &&
      rest[0] === DIAG_ID &&
      rest[1] === "explicacao-score-llm" &&
      rest[2] === "historico" &&
      method === "GET"
    ) {
      const items = explicacaoAtual
        ? [explicacaoAtual, narrativaAnterior]
        : [narrativaAnterior];
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ items }),
      });
      return;
    }

    if (rest.length === 0) {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([listaItem]),
      });
      return;
    }
    if (rest.length >= 2 && rest[rest.length - 1] === "retificacoes") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([]),
      });
      return;
    }

    if (
      rest.length >= 3 &&
      rest[0] === DIAG_ID &&
      rest[1] === "plano-acao" &&
      rest[2] === "kanban" &&
      method === "GET"
    ) {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(buildKanbanBoardMock()),
      });
      return;
    }

    if (
      rest.length >= 4 &&
      rest[0] === DIAG_ID &&
      rest[1] === "plano-acao" &&
      rest[3] === "comentarios" &&
      method === "GET"
    ) {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([]),
      });
      return;
    }

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(detalheBody(explicacaoAtual)),
    });
  });
}

async function loginPainelE2E(page: Page): Promise<void> {
  await page.goto("/login");
  await page.getByLabel(/E-mail Corporativo/i).fill("consultor@teste.com.br");
  await page.getByLabel(/^Senha$/i).fill("qualquer-senha");
  await page.getByRole("button", { name: /Entrar no Dashboard/i }).click();
}

test.describe("Painel empresa — expandir linha", () => {
  test("sem expandir não mostra ranking M05 (mock)", async ({ page }) => {
    await installPainelEmpresaApiMocks(page);
    await loginPainelE2E(page);

    await page.goto(`/dashboard/empresas/${CNPJ14}`);
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();

    await expect(
      page.getByRole("heading", { name: /Ranking explícito de gaps \(M05\)/i }),
    ).not.toBeVisible();
    await expect(page.getByText("Explicação do score (IA)")).not.toBeVisible();
    await expect(page.getByText("Autoconferência ABNT — 10 controles")).not.toBeVisible();
  });

  test("grelha abre ficha unificada da ação pelo título (mock)", async ({ page }) => {
    await installPainelEmpresaApiMocks(page);
    await loginPainelE2E(page);

    await page.goto(`/dashboard/empresas/${CNPJ14}`);
    const quadro = page.locator("#empresa-quadro-implantacao-principal");
    await expect(quadro).toBeVisible({ timeout: 15_000 });
    await quadro.getByRole("link", { name: "Controle ABNT M12 #1 (E2E)", exact: true }).click();

    await expect(page).toHaveURL(
      new RegExp(`/dashboard/empresas/${CNPJ14}/acao/${PLANO_ACAO_ID_1}`),
    );
    await expect(
      page.getByRole("heading", { level: 1, name: "Controle ABNT M12 #1 (E2E)", exact: true }),
    ).toBeVisible();
    await expect(page.getByRole("button", { name: "Salvar alterações" })).toBeVisible();
    await expect(page.getByText("Referência do motor")).toBeVisible();
    await expect(page.getByText("Em andamento")).toBeVisible();
  });

  test("menu Ações da grelha abre ficha unificada (mock)", async ({ page }) => {
    await installPainelEmpresaApiMocks(page);
    await loginPainelE2E(page);

    await page.goto(`/dashboard/empresas/${CNPJ14}`);
    const quadro = page.locator("#empresa-quadro-implantacao-principal");
    await expect(quadro).toBeVisible({ timeout: 15_000 });
    await quadro.getByRole("button", { name: "Ações" }).first().click();
    await page.getByRole("menuitem", { name: "Abrir ficha da ação" }).click();

    await expect(page).toHaveURL(
      new RegExp(`/dashboard/empresas/${CNPJ14}/acao/${PLANO_ACAO_ID_1}`),
    );
    await expect(
      page.getByRole("heading", { level: 1, name: "Controle ABNT M12 #1 (E2E)", exact: true }),
    ).toBeVisible();
  });

  test("vista empresa mostra quadro de implantação em grelha (mock)", async ({ page }) => {
    await installPainelEmpresaApiMocks(page);
    await loginPainelE2E(page);

    await page.goto(`/dashboard/empresas/${CNPJ14}`);
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    const quadro = page.locator("#empresa-quadro-implantacao-principal");
    await expect(quadro).toBeVisible({ timeout: 15_000 });
    await expect(quadro.locator("table")).toBeVisible();
    await expect(page.getByText(/Controle ABNT M12 #1/i).first()).toBeVisible();
  });

  test("menu Ações mostra opções sem ir à ficha (mock)", async ({ page }) => {
    await installPainelEmpresaApiMocks(page);
    await loginPainelE2E(page);

    await page.goto(`/dashboard/empresas/${CNPJ14}`);
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();

    await page.getByRole("button", { name: "Ações ▾" }).first().click();
    await expect(page.getByRole("menu").getByRole("menuitem", { name: "Retificações" })).toBeVisible();
    await expect(page.getByRole("menu").getByRole("menuitem", { name: "LGPD" })).toBeVisible();
    await expect(
      page.getByRole("menu").getByRole("menuitem", { name: "Abrir ficha do diagnóstico" }),
    ).toBeVisible();
  });

  test("expandir mostra ranking ou radar (mock)", async ({ page }) => {
    await installPainelEmpresaApiMocks(page);
    await loginPainelE2E(page);

    await page.goto(`/dashboard/empresas/${CNPJ14}`);
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();

    await page.getByRole("button", { name: /Expandir/i }).click();

    await expect(
      page.getByRole("heading", { name: /Ranking explícito de gaps \(M05\)/i }),
    ).toBeVisible({ timeout: 15_000 });
  });

  test("atalho LGPD no menu Ações abre painel centralizado (mock)", async ({ page }) => {
    await installPainelEmpresaApiMocks(page);
    await loginPainelE2E(page);

    await page.goto(`/dashboard/empresas/${CNPJ14}`);
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();

    await page.getByRole("button", { name: /Expandir/i }).click();
    await expect(
      page.getByRole("heading", { name: /Ranking explícito de gaps \(M05\)/i }),
    ).toBeVisible({ timeout: 15_000 });

    await page.getByRole("button", { name: "Ações ▾" }).first().click();
    const lgpdHref = await page.getByRole("menuitem", { name: "LGPD" }).getAttribute("href");
    expect(lgpdHref).toMatch(/privacidade/);
    await page.goto(lgpdHref!);

    await expect(page).toHaveURL(
      new RegExp(`/dashboard/privacidade\\?.*diagnostico_id=${DIAG_ID}`),
    );
    await expect(page.getByRole("heading", { name: "Privacidade LGPD" })).toBeVisible({
      timeout: 15_000,
    });
    await expect(page.locator("#priv-lgpd-registrar")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByText("Nova solicitação")).toBeVisible();
  });

  test("expandir mostra explicação score LLM e histórico (perfil avançado)", async ({ page }) => {
    await installPainelEmpresaApiMocks(page, {
      explicacaoInicial: narrativaLlm,
      perfilConta: "avancado",
    });
    await loginPainelE2E(page);

    await page.goto(`/dashboard/empresas/${CNPJ14}`);
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();

    await page.getByRole("button", { name: /Expandir/i }).click();
    await expect(page.getByText("Explicação do score (IA)")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByRole("region", { name: "Texto da explicação do score" })).toContainText(
      "dimensão fiscal",
    );
    await expect(page.getByText("Gerações anteriores (1)")).toBeVisible();
    await page.getByText("Gerações anteriores (1)").click();
    await expect(page.getByText("Versão anterior da narrativa fiscal.")).toBeVisible();
  });
});
