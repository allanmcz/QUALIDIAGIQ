import { test, expect } from '@playwright/test';

test('Wizard E2E Flow', async ({ page }) => {
  page.on('console', msg => console.log('BROWSER CONSOLE:', msg.text()));
  console.log("Navigating to Wizard...");
  await page.goto("http://127.0.0.1:3010/wizard");

  // Step 1
  console.log("Filling Step 1...");
  await page.fill('input[id="cnpj"]', '33000167000101');
  await page.fill('input[id="razao_social"]', 'Empresa E2E Test SA');
  await page.fill('input[id="nome"]', 'Test Lead');
  await page.fill('input[id="email"]', 'test@e2e.com');
  
  await page.getByRole('button', { name: 'Próxima Etapa' }).click();

  // Wait a bit and take screenshot to see errors
  await page.waitForTimeout(1000);
  await page.screenshot({ path: "test-results/step1-error.png" });

  // Step 2
  console.log("Filling Step 2...");
  await page.locator('select[id="porte"]').selectOption('medio');
  await page.locator('select[id="regime"]').selectOption('lucro_real');
  await page.locator('select[id="setor_macro"]').selectOption('servicos');
  await page.locator('select[id="uf"]').selectOption('SP');
  await page.fill('input[id="cnae_principal"]', '1234567');
  
  await page.getByRole('button', { name: 'Próxima Etapa' }).click();

  // Step 3
  console.log("Filling Step 3...");
  const radios = await page.locator('input[type="radio"]').all();
  // Select the highest score for each question
  await radios[2].check();
  await radios[5].check();
  await radios[8].check();

  console.log("Submitting...");
  await page.getByRole('button', { name: 'Finalizar Diagnóstico' }).click();

  console.log("Waiting for success page...");
  await expect(page.getByText('Diagnóstico Concluído com Sucesso!')).toBeVisible({ timeout: 15000 });
  console.log("SUCCESS: Reached the success page and API request succeeded!");
});
