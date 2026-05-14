import { expect, test } from "@playwright/test";

import { installMockBffPainelLogin } from "./helpers/mock_bff_painel_auth";
import { installMockListaDiagnosticosGet } from "./helpers/mock_diagnosticos_lista_get";

/** Evita overlay de rascunho e estado partilhado entre workers. */
async function limparArmazenamentoBrowser(page: import("@playwright/test").Page): Promise<void> {
  await page.context().clearCookies();
  await page.addInitScript(() => {
    try {
      localStorage.clear();
      sessionStorage.clear();
    } catch {
      /* ignore */
    }
  });
}

/** Área de conteúdo (`main` no layout raiz) — evita falso positivo do header/footer em viewports estreitas. */
async function assertConteudoPrincipalSemOverflowHorizontal(
  page: import("@playwright/test").Page,
): Promise<void> {
  const excede = await page.evaluate(() => {
    const main = document.querySelector("main");
    if (!main) return false;
    return main.scrollWidth > main.clientWidth + 2;
  });
  expect(
    excede,
    "main não deve exceder a largura útil (scroll horizontal no conteúdo principal)",
  ).toBe(false);
}

test.describe("Smoke mobile (viewport estreito)", () => {
  test.beforeEach(async ({ page }) => {
    await limparArmazenamentoBrowser(page);
  });

  test("/wizard — sem overflow horizontal, CTA e avanço do passo 1", async ({ page }) => {
    await page.goto("/wizard");
    await expect(
      page.getByRole("heading", { name: /Análise de Maturidade Tributária/i }),
    ).toBeVisible();

    await assertConteudoPrincipalSemOverflowHorizontal(page);

    const cnpjOpcional = page.getByRole("textbox", { name: /CNPJ/i });
    await cnpjOpcional.click();
    await cnpjOpcional.fill("");

    const proxima = page.getByRole("button", { name: /Próxima Etapa/i });
    await expect(proxima).toBeVisible();

    await page.getByLabel(/Razão Social/i).fill("Empresa Smoke Mobile LTDA");
    await page.getByLabel(/^Seu Nome/i).fill("Utilizador Mobile");
    await page.getByLabel(/E-mail Profissional/i).fill("mobile.smoke@e2e.qualidiagiq.test");
    await page.locator("#lgpd").check({ force: true });

    await proxima.click();
    await expect(page.getByRole("heading", { name: /Perfil da Empresa/i })).toBeVisible({ timeout: 20_000 });
  });

  test("/login — campos e botão visíveis no viewport móvel", async ({ page }) => {
    await page.goto("/login");
    await assertConteudoPrincipalSemOverflowHorizontal(page);
    await expect(page.getByLabel(/E-mail Corporativo/i)).toBeVisible();
    await expect(page.getByRole("button", { name: /Entrar no Dashboard/i })).toBeVisible();
  });

  test("/dashboard sem sessão — redirecciona para /login", async ({ page }) => {
    await page.goto("/dashboard/diagnosticos");
    await page.waitForURL(/\/login/i, { timeout: 15_000 });
    expect(page.url()).toMatch(/\/login/);
    await expect(page.getByLabel(/E-mail Corporativo/i)).toBeVisible();
  });

  test("/dashboard com mock BFF — layout do painel não quebra", async ({ page }) => {
    await installMockBffPainelLogin(page, {
      tokenParaUpstream: "e2e-mobile-smoke",
      nome: "Consultor Mobile",
    });
    await installMockListaDiagnosticosGet(page, []);

    await page.goto("/login");
    await page.getByLabel(/E-mail Corporativo/i).fill("mobile@e2e.qualidiagiq.test");
    await page.getByLabel(/^Senha$/i).fill("qualquer");
    await page.getByRole("button", { name: /Entrar no Dashboard/i }).click();

    await page.waitForURL("**/dashboard/diagnosticos**", { timeout: 20_000 });
    await assertConteudoPrincipalSemOverflowHorizontal(page);
    await expect(page.getByRole("heading", { name: /Painel de diagnósticos/i })).toBeVisible();
  });
});
