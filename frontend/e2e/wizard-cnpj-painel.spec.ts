import { expect, test } from "@playwright/test";

/**
 * Metadados de sessão painel (BFF) — alinhado a `persistPainelSessionMetadataOnly` / `temSessaoPainelParaApiCliente`.
 * Não usar JWT fictício em `admin_token`: o fluxo novo não persiste token em `localStorage`.
 */
const LS_PERFIL = "admin_perfil_conta";
const LS_NOME = "admin_nome";
const LS_EMAIL = "admin_email";

test.describe("Wizard — ADR-013 CNPJ com sessão na plataforma", () => {
  test("passo 1 sem CNPJ não avança quando há sessão de painel (metadados)", async ({ page }) => {
    await page.addInitScript(
      ([perfil, nome, email]: [string, string, string]) => {
        window.localStorage.setItem(perfil, "gratuito");
        window.localStorage.setItem(nome, "QA E2E ADR-013");
        window.localStorage.setItem(email, "fulano.qa@example.com");
      },
      [LS_PERFIL, LS_NOME, LS_EMAIL],
    );

    await page.goto("/wizard");

    const dialog = page.getByRole("dialog", {
      name: /Diagnóstico em andamento neste navegador/i,
    });
    if (await dialog.isVisible()) {
      await dialog.getByRole("button", { name: /Reiniciar diagnóstico/i }).click();
    }

    await page.getByLabel(/Razão Social \*/i).fill("Empresa E2E Painel LTDA");
    await page.getByRole("textbox", { name: /CNPJ/i }).fill("");
    await page.getByLabel(/Seu Nome \*/i).fill("Fulano QA");
    await page.getByLabel(/E-mail Profissional \*/i).fill("fulano.qa@example.com");
    await page.getByRole("checkbox", { name: /Declaro que li e aceito/i }).check();

    await page.getByRole("button", { name: "Próxima Etapa" }).click();

    await expect(
      page.getByText(/Com sessão na plataforma, o CNPJ é obrigatório|histórico por empresa no painel/i).first(),
    ).toBeVisible();
  });
});
