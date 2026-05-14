import type { Page } from "@playwright/test";
import { expect } from "@playwright/test";

/**
 * Preenche o CNPJ no passo 1 do wizard (rótulo «CNPJ *» com sessão ou «CNPJ (opcional)» sem sessão).
 * `locator('#cnpj').fill` falhou de forma intermitente com react-hook-form em E2E paralelos.
 */
export async function fillWizardCnpjPasso1(page: Page, digitos = "12345678000195"): Promise<void> {
  const cnpjInput = page.getByRole("textbox", { name: /CNPJ/i });
  await cnpjInput.click();
  await cnpjInput.fill("");
  await cnpjInput.fill(digitos);
  await expect(cnpjInput).not.toHaveValue("");
}
