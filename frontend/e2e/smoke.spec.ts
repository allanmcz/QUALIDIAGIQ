import { test, expect } from "@playwright/test";

test.describe("Smoke QDI", () => {
  test("wizard exibe título e formulário", async ({ page }) => {
    await page.goto("/wizard");
    await expect(
      page.getByRole("heading", { name: /Análise de Maturidade Tributária/i }),
    ).toBeVisible();
    await expect(page.getByRole("main").first()).toBeVisible();
  });

  test("login carrega campos de autenticação", async ({ page }) => {
    await page.goto("/login");
    await expect(page.getByLabel(/E-mail Corporativo/i)).toBeVisible();
    await expect(
      page.getByRole("button", { name: /Entrar no Dashboard/i }),
    ).toBeVisible();
  });
});
