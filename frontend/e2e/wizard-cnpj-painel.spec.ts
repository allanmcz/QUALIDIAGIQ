import { expect, test } from "@playwright/test";

/** Mesma chave que `frontend/lib/api/config.ts` — evitar import no runner E2E. */
const ADMIN_TOKEN_STORAGE_KEY = "admin_token";

test.describe("Wizard — ADR-013 CNPJ com sessão na plataforma", () => {
  test("passo 1 sem CNPJ não avança quando há token de painel no armazenamento", async ({
    page,
  }) => {
    await page.addInitScript((key: string) => {
      window.localStorage.setItem(
        key,
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.signature-placeholder",
      );
    }, ADMIN_TOKEN_STORAGE_KEY);

    await page.goto("/wizard");

    const dialog = page.getByRole("dialog", {
      name: /Diagnóstico em andamento neste navegador/i,
    });
    if (await dialog.isVisible()) {
      await dialog.getByRole("button", { name: /Reiniciar diagnóstico/i }).click();
    }

    await page.getByLabel(/Razão Social \*/i).fill("Empresa E2E Painel LTDA");
    await page.locator("#cnpj").fill("");
    await page.getByLabel(/Seu Nome \*/i).fill("Fulano QA");
    await page.getByLabel(/E-mail Profissional \*/i).fill("fulano.qa@example.com");
    await page.getByRole("checkbox", { name: /Declaro que li e aceito/i }).check();

    await page.getByRole("button", { name: "Próxima Etapa" }).click();

    await expect(
      page.getByText(
        /Com sessão na plataforma, o CNPJ é obrigatório|histórico por empresa no painel/i,
      ),
    ).toBeVisible();
  });
});
