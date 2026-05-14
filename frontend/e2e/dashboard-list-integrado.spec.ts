import { test, expect } from "@playwright/test";

/**
 * C1 — fluxo contra API Python real (Postgres + seed CI), sem `page.route`.
 * Ative com `PLAYWRIGHT_INTEGRATED=1`, API em `NEXT_PUBLIC_API_URL` e Next em `PLAYWRIGHT_BASE_URL`.
 */
const integrado = process.env.PLAYWRIGHT_INTEGRATED === "1";

test.describe("Dashboard lista (API integrada CI)", () => {
  test.skip(!integrado, "defina PLAYWRIGHT_INTEGRATED=1, NEXT_PUBLIC_API_URL e suba API + Next");

  test("login → lista diagnósticos (sem mock)", async ({ page }) => {
    await page.goto("/login");
    await page.getByLabel(/E-mail Corporativo/i).fill("ci-dashboard@qualidiagiq.test");
    await page.getByLabel(/^Senha$/i).fill("secret");
    await page.getByRole("button", { name: /Entrar no Dashboard/i }).click();
    /** Login BFF faz `router.push` para `/dashboard/diagnosticos` — não usar `goto(/dashboard)` em seguida (cancela a navegação cliente e fica sem cookie aplicado). */
    await page.waitForURL("**/dashboard/diagnosticos**", { timeout: 20_000 });

    await expect(page.getByRole("heading", { name: /Painel de Diagnósticos/i })).toBeVisible();
    await expect(page.getByText("Carregando lista…")).toBeHidden({ timeout: 30_000 });

    /**
     * Com `DATABASE_URL`, a API usa `PostgresDiagnosticoRepository` — a lista pode estar vazia em dev local.
     * Sem DSN e `QDI_CI_PLAYWRIGHT_INTEGRATED=1`, o seed em memória expõe «Empresa Lista CI Integrado SA».
     */
    const seedEmpresa = page.getByText("Empresa Lista CI Integrado SA");
    const listaVazia = page.getByText(/Nenhum diagnóstico neste painel ainda/);
    const cartaoDiagnostico = page.locator("div.grid").locator("a[href^='/dashboard/diagnosticos/']").first();

    await expect(seedEmpresa.or(listaVazia).or(cartaoDiagnostico)).toBeVisible({ timeout: 15_000 });

    if (await seedEmpresa.isVisible()) {
      await expect(page.getByText(/68\.5\/100/)).toBeVisible();
    }
  });
});
