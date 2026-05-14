import { test, expect } from "@playwright/test";

import { installMockBffPainelCadastro } from "./helpers/mock_bff_painel_auth";
import { installMockListaDiagnosticosGet } from "./helpers/mock_diagnosticos_lista_get";

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

  test("cadastro carrega nome, e-mail e senha", async ({ page }) => {
    await page.goto("/cadastro");
    await expect(page.getByLabel(/^Nome$/i)).toBeVisible();
    await expect(page.getByLabel(/^E-mail$/i)).toBeVisible();
    await expect(page.getByRole("button", { name: /Cadastrar e entrar/i })).toBeVisible();
  });

  test("cadastro BFF mock: submete e abre painel de diagnósticos", async ({ page }) => {
    await installMockBffPainelCadastro(page, {
      tokenParaUpstream: "e2e-smoke-cadastro",
      nome: "Utilizador Smoke Cadastro",
    });
    await installMockListaDiagnosticosGet(page, []);

    await page.goto("/cadastro");
    await page.getByLabel(/^Nome$/i).fill("Utilizador Smoke Cadastro");
    await page.getByLabel(/^E-mail$/i).fill("smoke.cadastro@e2e.qualidiagiq.test");
    await page.getByLabel(/^Senha$/i).fill("senha1234");
    await page.getByRole("button", { name: /Cadastrar e entrar/i }).click();

    await page.waitForURL("**/dashboard/diagnosticos**", { timeout: 15_000 });
    await expect(page.getByRole("heading", { name: /Painel de diagnósticos/i })).toBeVisible();
    await expect(page.getByText(/Nenhum diagnóstico neste painel ainda/i)).toBeVisible();
  });

  test("landing: cabeçalho com links Cadastrar e Entrar", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("link", { name: /^Cadastrar$/i })).toHaveAttribute("href", "/cadastro");
    const entrar = page.getByRole("link", { name: /^Entrar$/i });
    await expect(entrar).toBeVisible();
    await expect(entrar).toHaveAttribute("href", /\/login/);
  });

  test("/metodologia exibe título (API opcional no CI)", async ({ page }) => {
    await page.goto("/metodologia");
    await expect(page.getByRole("heading", { name: /Como calculamos a sua maturidade tributária/i })).toBeVisible();
  });

  test("/termos exibe título MVP", async ({ page }) => {
    await page.goto("/termos");
    await expect(page.getByRole("heading", { name: /Termos de uso/i })).toBeVisible();
  });

  test("/privacidade exibe título MVP", async ({ page }) => {
    await page.goto("/privacidade");
    await expect(page.getByRole("heading", { name: /Política de privacidade/i })).toBeVisible();
  });

  test("/avaliacao-contador exibe guia para contadores", async ({ page }) => {
    await page.goto("/avaliacao-contador");
    await expect(
      page.getByRole("heading", { name: /Avaliação para contadores e fiscalistas/i }),
    ).toBeVisible();
  });
});
