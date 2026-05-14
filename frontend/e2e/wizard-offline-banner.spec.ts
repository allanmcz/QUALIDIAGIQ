import { test, expect } from "@playwright/test";

test.describe("Wizard — banner sem ligação (offline)", () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      try {
        window.localStorage.clear();
        window.sessionStorage.clear();
      } catch {
        /* ignore */
      }
    });
  });

  test("Playwright offline mostra aviso de rede e oculta ao voltar online", async ({
    page,
    context,
  }) => {
    await page.goto("/wizard");

    await context.setOffline(true);
    const aviso = page.getByRole("status").filter({
      hasText: /Sem ligação à Internet/i,
    });
    await expect(aviso).toBeVisible();
    await expect(aviso).toContainText(/consulta CNPJ/i);

    await context.setOffline(false);
    await expect(aviso).toBeHidden();
  });
});
