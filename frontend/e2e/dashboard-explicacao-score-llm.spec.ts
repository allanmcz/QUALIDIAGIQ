import type { Page } from "@playwright/test";
import { expect, test } from "@playwright/test";

import { installMockBffPainelLogin } from "./helpers/mock_bff_painel_auth";
import { painelInterceptarUrlApiDiagnosticos } from "./helpers/painel_api_diagnosticos_url";

const DIAG_ID = "33333333-3333-4333-a333-333333333333";
const CNPJ14 = "12345678000195";

const listaItem = {
  id: DIAG_ID,
  empresa_razao_social: "Empresa E2E Explicação LLM",
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

const narrativaAnterior = {
  text: "Versão anterior da narrativa fiscal.",
  provider: "fake",
  model: "fake-llm",
  policy_version: "2026-05-14-v1",
  input_tokens: 1,
  output_tokens: 2,
  estimated_cost_usd: 0,
  latency_ms: 8,
  blocked_by_guardrail: false,
  guardrail_reason: null,
  guardrail_status: "ok",
  gerado_em: "2026-05-14T10:00:00+00:00",
  trace_id: "e2e-trace-explic-ant",
};

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
  trace_id: "e2e-trace-explic",
};

function detalheBody(
  explicacao: typeof narrativaLlm | null,
  plano: "gratuito" | "avancado" = "gratuito",
) {
  return {
    id: DIAG_ID,
    empresa_razao_social: "Empresa E2E Explicação LLM",
    empresa_cnpj: CNPJ14,
    status: "finalizado",
    plano,
    versao_otimista: 1,
    relatorio_pdf_url: null,
    checklist_m12_autoconf: null,
    quadro_implantacao_anotacoes: null,
    matriz_impacto: [],
    cronograma: [],
    explicacao_score_llm: explicacao,
    score: {
      score_geral: { valor: 52 },
      score_por_dimensao: {
        fiscal: { valor: 42, peso_total_aplicado: 1.5 },
        tecnologica: { valor: 62, peso_total_aplicado: 1.3 },
      },
    },
    checklist: [],
  };
}

async function loginPainel(page: Page): Promise<void> {
  await page.goto("/login");
  await page.getByLabel(/E-mail Corporativo/i).fill("consultor@teste.com.br");
  await page.getByLabel(/^Senha$/i).fill("qualquer-senha");
  await page.getByRole("button", { name: /Entrar no Dashboard/i }).click();
  await page.waitForURL("**/dashboard/**", { timeout: 20_000 });
}

/** Rota legada redireciona para vista unificada por CNPJ com ciclo expandido. */
async function abrirVistaEmpresaUnificada(
  page: Page,
  opts?: { viaRedirectLegado?: boolean },
): Promise<void> {
  if (opts?.viaRedirectLegado) {
    await page.goto(`/dashboard/diagnosticos/${DIAG_ID}`);
    await expect(page).toHaveURL(new RegExp(`/dashboard/empresas/${CNPJ14}.*expand=${DIAG_ID}`));
    return;
  }
  await page.goto(`/dashboard/empresas/${CNPJ14}?expand=${DIAG_ID}`);
}

type InstallMocksOpts = {
  explicacaoInicial: typeof narrativaLlm | null;
  /** Perfil da conta na plataforma (gate tier no card). */
  perfilConta?: "gratuito" | "avancado";
  /** Plano persistido do diagnóstico (segundo braço do gate — ADR tier B). */
  planoDiagnostico?: "gratuito" | "avancado";
};

/** Espelha ``pode_gerar_explicacao_score_llm`` (application) / ``sessaoPodeExplicacaoScore`` (UI). */
function tierNegadoNoMock(opts: InstallMocksOpts): boolean {
  const perfil = opts.perfilConta ?? "avancado";
  if (perfil === "avancado") return false;
  const plano = opts.planoDiagnostico ?? "gratuito";
  return plano !== "avancado";
}

async function installMocks(page: Page, opts: InstallMocksOpts) {
  await installMockBffPainelLogin(page, {
    tokenParaUpstream: "e2e-explic-llm-token",
    nome: "Consultor QA",
    perfil_conta: opts.perfilConta ?? "avancado",
    limparLocalStoragePainelAntesDeCadaDocumento: true,
  });

  await page.route("**/privacidade/solicitacoes**", async (route) => {
    if (route.request().method() === "GET") {
      await route.fulfill({ status: 200, contentType: "application/json", body: "[]" });
      return;
    }
    await route.continue();
  });

  let explicacaoAtual = opts.explicacaoInicial;

  await page.route(painelInterceptarUrlApiDiagnosticos, async (route) => {
    const method = route.request().method();
    const pathname = new URL(route.request().url()).pathname.replace(/\/$/, "");
    // Não interceptar UI `/dashboard/diagnosticos/...` — o glob apanha também a navegação Next.
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

    if (rest.length >= 2 && rest[0] === DIAG_ID && rest[1] === "explicacao-score-llm") {
      if (method === "POST") {
        const key = route.request().headers()["idempotency-key"];
        expect(key).toBeTruthy();
        if (tierNegadoNoMock(opts)) {
          await route.fulfill({
            status: 403,
            contentType: "application/json",
            body: JSON.stringify({
              detail:
                "Explicação do score por IA está disponível no plano avançado da conta na plataforma (perfil avançado ou diagnóstico Plus). Faça upgrade para desbloquear.",
            }),
          });
          return;
        }
        explicacaoAtual = { ...narrativaLlm };
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(explicacaoAtual),
        });
        return;
      }
      await route.continue();
      return;
    }

    if (rest.length >= 2 && rest[rest.length - 1] === "retificacoes" && method === "GET") {
      await route.fulfill({ status: 200, contentType: "application/json", body: "[]" });
      return;
    }

    if (rest.length === 0 && method === "GET") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([listaItem]),
      });
      return;
    }

    if (rest.length === 1 && rest[0] === DIAG_ID && method === "GET") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(
          detalheBody(explicacaoAtual, opts.planoDiagnostico ?? "gratuito"),
        ),
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
        body: JSON.stringify({ diagnostico_id: DIAG_ID, cards: [] }),
      });
      return;
    }

    if (rest.length >= 2 && rest[rest.length - 1] === "retificacoes" && method === "GET") {
      await route.fulfill({ status: 200, contentType: "application/json", body: "[]" });
      return;
    }

    await route.continue();
  });
}

test.describe("Painel — explicação score LLM", () => {
  test("hidrata narrativa persistida ao abrir ficha", async ({ page }) => {
    await installMocks(page, { explicacaoInicial: narrativaLlm });
    await loginPainel(page);
    await abrirVistaEmpresaUnificada(page, { viaRedirectLegado: true });
    await expect(page.getByRole("region", { name: "Texto da explicação do score" })).toContainText(
      "dimensão fiscal",
    );
    await expect(page.getByText("Última geração:")).toBeVisible();
  });

  test("exibe gerações anteriores no histórico colapsável", async ({ page }) => {
    await installMocks(page, { explicacaoInicial: narrativaLlm });
    await loginPainel(page);
    await abrirVistaEmpresaUnificada(page);
    await expect(page.getByText("Gerações anteriores (1)")).toBeVisible();
    await page.getByText("Gerações anteriores (1)").click();
    await expect(page.getByText("Versão anterior da narrativa fiscal.")).toBeVisible();
  });

  test("gerar explicação via POST mockado", async ({ page }) => {
    await installMocks(page, { explicacaoInicial: null });
    await loginPainel(page);
    await abrirVistaEmpresaUnificada(page);
    await page.getByRole("button", { name: "Gerar explicação" }).click();
    await expect(page.getByRole("region", { name: "Texto da explicação do score" })).toContainText(
      "dimensão fiscal",
    );
  });

  test("perfil gratuito vê upgrade e não aciona POST de explicação", async ({ page }) => {
    let postExplicacao = 0;
    await installMocks(page, { explicacaoInicial: null, perfilConta: "gratuito" });
    await page.route("**/diagnosticos/**/explicacao-score-llm", async (route) => {
      const pathname = new URL(route.request().url()).pathname.replace(/\/$/, "");
      if (pathname.includes("/dashboard/diagnosticos")) {
        await route.continue();
        return;
      }
      if (route.request().method() === "POST") {
        postExplicacao += 1;
      }
      await route.continue();
    });
    await loginPainel(page);
    await abrirVistaEmpresaUnificada(page);
    await expect(
      page.getByText(/Explicação do score por IA está disponível no/i),
    ).toBeVisible();
    await expect(page.getByText(/plano avançado/i).first()).toBeVisible();
    await expect(page.getByRole("button", { name: /Gerar explicação/i })).toHaveCount(0);
    await expect(page.getByText("Gerações anteriores")).toHaveCount(0);
    expect(postExplicacao).toBe(0);
  });

  test("perfil gratuito não vê narrativa do GET sem acesso (tier)", async ({ page }) => {
    await installMocks(page, {
      explicacaoInicial: narrativaLlm,
      perfilConta: "gratuito",
      planoDiagnostico: "gratuito",
    });
    await loginPainel(page);
    await abrirVistaEmpresaUnificada(page);
    await expect(
      page.getByText(/Explicação do score por IA está disponível no/i),
    ).toBeVisible();
    await expect(page.getByRole("region", { name: "Texto da explicação do score" })).toHaveCount(
      0,
    );
    await expect(page.getByText("Última geração:")).toHaveCount(0);
    await expect(page.getByText(/dimensão fiscal/i)).toHaveCount(0);
  });

  test("perfil gratuito com diagnóstico avançado gera explicação (POST 200)", async ({ page }) => {
    await installMocks(page, {
      explicacaoInicial: null,
      perfilConta: "gratuito",
      planoDiagnostico: "avancado",
    });
    await loginPainel(page);
    await abrirVistaEmpresaUnificada(page);
    await expect(page.getByText(/Faça upgrade para desbloquear/i)).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Gerar explicação" })).toBeVisible();
    await page.getByRole("button", { name: "Gerar explicação" }).click();
    await expect(page.getByRole("region", { name: "Texto da explicação do score" })).toContainText(
      "dimensão fiscal",
    );
    await expect(page.getByText("Última geração:")).toBeVisible();
  });
});
