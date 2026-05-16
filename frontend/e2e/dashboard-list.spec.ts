import { test, expect } from "@playwright/test";

import { installMockBffPainelLogin } from "./helpers/mock_bff_painel_auth";
import { installMockListaDiagnosticosGet } from "./helpers/mock_diagnosticos_lista_get";

/**
 * Plano ANALISE §G — smoke dashboard com GET /diagnosticos/ mockado (sem API real).
 */
test.describe("Dashboard lista (mock API)", () => {
  test("carrega cards a partir da API mockada", async ({ page }) => {
    await installMockBffPainelLogin(page, {
      tokenParaUpstream: "e2e-dashboard-token",
      nome: "Consultor QA",
      limparLocalStoragePainelAntesDeCadaDocumento: true,
    });

    await installMockListaDiagnosticosGet(page, [
      {
        id: "11111111-1111-4111-a111-111111111111",
        empresa_razao_social: "Empresa Lista E2E",
        status: "finalizado",
        plano: "gratuito",
        score_geral: 68.5,
        criado_em: "2026-05-05T12:00:00Z",
        finalizado_em: "2026-05-05T12:05:00Z",
        relatorio_pdf_url: null,
      },
    ]);

    await page.goto("/login");
    await page.getByLabel(/E-mail Corporativo/i).fill("consultor@teste.com.br");
    await page.getByLabel(/^Senha$/i).fill("qualquer-senha");
    await page.getByRole("button", { name: /Entrar no Dashboard/i }).click();

    await page.goto("/dashboard");
    await expect(page.getByRole("heading", { name: /Painel de Diagnósticos/i })).toBeVisible();
    await expect(page.getByText("Empresa Lista E2E")).toBeVisible();
    await expect(page.getByText(/68\.5\/100/)).toBeVisible();
  });
});
