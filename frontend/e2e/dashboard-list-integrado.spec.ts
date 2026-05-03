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

    await page.goto("/dashboard");
    await expect(page.getByRole("heading", { name: /Painel de Diagnósticos/i })).toBeVisible();
    await expect(page.getByText("Empresa Lista CI Integrado SA")).toBeVisible();
    await expect(page.getByText(/68\.5\/100/)).toBeVisible();
  });
});
