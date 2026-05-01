import { test, expect } from "@playwright/test";

test.describe("Smoke QDI", () => {
  test("landing CTA Metodologia aponta para /metodologia", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("link", { name: /Conhecer a Metodologia/i })).toHaveAttribute("href", "/metodologia");
  });

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

  test("/metodologia exibe título (API opcional no CI)", async ({ page }) => {
    await page.goto("/metodologia");
    await expect(page.getByRole("heading", { name: /Metodologia e manifesto de pesos/i })).toBeVisible();
  });

  test("/termos exibe título MVP", async ({ page }) => {
    await page.goto("/termos");
    await expect(page.getByRole("heading", { name: /Termos de uso/i })).toBeVisible();
  });

  test("/privacidade exibe título MVP", async ({ page }) => {
    await page.goto("/privacidade");
    await expect(page.getByRole("heading", { name: /Política de privacidade/i })).toBeVisible();
  });
});
