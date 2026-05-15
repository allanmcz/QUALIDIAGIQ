import type { Page } from "@playwright/test";
import { expect, test } from "@playwright/test";

import { installMockBffPainelLogin } from "./helpers/mock_bff_painel_auth";

const DIAG_ID = "33333333-3333-4333-a333-333333333333";
const CNPJ14 = "12345678000195";

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

function detalheBody(explicacao: typeof narrativaLlm | null) {
  return {
    id: DIAG_ID,
    empresa_razao_social: "Empresa E2E Explicação LLM",
    empresa_cnpj: CNPJ14,
    status: "finalizado",
    plano: "gratuito",
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

async function installMocks(page: Page, opts: { explicacaoInicial: typeof narrativaLlm | null }) {
  await installMockBffPainelLogin(page, {
    tokenParaUpstream: "e2e-explic-llm-token",
    nome: "Consultor QA",
  });

  await page.route("**/privacidade/solicitacoes**", async (route) => {
    if (route.request().method() === "GET") {
      await route.fulfill({ status: 200, contentType: "application/json", body: "[]" });
      return;
    }
    await route.continue();
  });

  let explicacaoAtual = opts.explicacaoInicial;

  await page.route("**/diagnosticos/**", async (route) => {
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

    if (rest.length >= 2 && rest[0] === DIAG_ID && rest[1] === "explicacao-score-llm") {
      if (method === "POST") {
        const key = route.request().headers()["idempotency-key"];
        expect(key).toBeTruthy();
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

    if (rest.length === 1 && rest[0] === DIAG_ID && method === "GET") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(detalheBody(explicacaoAtual)),
      });
      return;
    }

    await route.continue();
  });
}

test.describe("Painel — explicação score LLM", () => {
  test("hidrata narrativa persistida ao abrir ficha", async ({ page }) => {
    await installMocks(page, { explicacaoInicial: narrativaLlm });
    await loginPainel(page);
    await page.goto(`/dashboard/diagnosticos/${DIAG_ID}`);
    await expect(page.getByRole("region", { name: "Texto da explicação do score" })).toContainText(
      "dimensão fiscal",
    );
    await expect(page.getByText("Última geração:")).toBeVisible();
  });

  test("gerar explicação via POST mockado", async ({ page }) => {
    await installMocks(page, { explicacaoInicial: null });
    await loginPainel(page);
    await page.goto(`/dashboard/diagnosticos/${DIAG_ID}`);
    await page.getByRole("button", { name: "Gerar explicação" }).click();
    await expect(page.getByRole("region", { name: "Texto da explicação do score" })).toContainText(
      "dimensão fiscal",
    );
  });
});
