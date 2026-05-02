import { test, expect } from "@playwright/test";

/**
 * P8 — painel “validar âncora” no passo 3 do wizard (NEXT_PUBLIC_WIZARD_NORMATIVA).
 * CI padrão não define PLAYWRIGHT_WIZARD_NORMATIVA — suite inteira ignorada.
 * Local: PLAYWRIGHT_WIZARD_NORMATIVA=1 npm run test:e2e -- e2e/wizard-normativa.spec.ts
 */

const PID_TERNARIA = "cafe0001-0001-4001-8001-000000000001";
const PID_ESCALA = "cafe0002-0002-4002-8002-000000000002";

const enabled = process.env.PLAYWRIGHT_WIZARD_NORMATIVA === "1";

(enabled ? test.describe : test.describe.skip)("Wizard P8 âncora normativa (flag)", () => {
  test("passo 3 exibe painel e POST /normativa/validar-ancora retorna feedback", async ({
    page,
  }) => {
    test.setTimeout(60_000);
    let normativaHits = 0;

    await page.route("**/auth/login", async (route) => {
      if (route.request().method() !== "POST") {
        await route.continue();
        return;
      }
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          access_token: "e2e-token-normativa",
          nome: "Usuário E2E",
        }),
      });
    });

    await page.route("**/normativa/validar-ancora", async (route) => {
      if (route.request().method() !== "POST") {
        await route.continue();
        return;
      }
      normativaHits += 1;
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ valido: true, motivo_rejeicao: null }),
      });
    });

    /**
     * Playwright avalia da última rota registrada para a primeira.
     * O handler amplo em diagnosticos deve ser registrado antes do GET questionário;
     * caso contrário o GET cai no handler genérico (method !== POST → continue) e vira "Failed to fetch".
     */
    await page.route("**/diagnosticos**", async (route) => {
      const u = route.request().url();
      if (
        route.request().method() !== "POST" ||
        u.includes("questionario") ||
        u.includes("metodologia") ||
        u.includes("manifesto-pesos")
      ) {
        await route.continue();
        return;
      }
      await route.fulfill({
        status: 201,
        contentType: "application/json",
        body: JSON.stringify({
          id: "deadbeef-dead-dead-dead-deadbeefdead",
          status: "finalizado",
          plano: "gratuito",
          empresa_razao_social: "Empresa E2E LTDA",
          score: {
            score_geral: { valor: 80, peso_total_aplicado: 1 },
            score_por_dimensao: { fiscal: { valor: 80, peso_total_aplicado: 1 } },
          },
          relatorio_pdf_url: null,
          recomendacao_ia: null,
          checklist: [],
          matriz_impacto: [],
          cronograma: [],
          hash_evidencia: null,
          versao_otimista: null,
        }),
      });
    });

    await page.route("**/diagnosticos/questionario*", async (route) => {
      if (route.request().method() !== "GET") {
        await route.continue();
        return;
      }
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          versao_catalogo: "e2e-normativa",
          total: 2,
          perguntas: [
            {
              id: PID_TERNARIA,
              codigo: "Q-E2E-T",
              texto: "Pergunta ternária E2E",
              tipo: "ternaria",
              peso: 1,
              dimensao: "fiscal",
              base_legal: null,
              multipla_total: null,
              opcoes: null,
            },
            {
              id: PID_ESCALA,
              codigo: "Q-E2E-E",
              texto: "Pergunta escala E2E",
              tipo: "escala_1_5",
              peso: 1,
              dimensao: "fiscal",
              base_legal: null,
              multipla_total: null,
              opcoes: null,
            },
          ],
        }),
      });
    });

    await page.goto("/login");
    await page.getByLabel(/E-mail Corporativo/i).fill("e2e@teste.com");
    await page.locator("#password").fill("qualquer");
    await page.getByRole("button", { name: /Entrar no Dashboard/i }).click();
    await page.waitForURL("**/dashboard**", { timeout: 15_000 });

    await page.goto("/wizard");

    await page.locator("#cnpj").fill("12345678000195");
    await page.locator("#razao_social").fill("Empresa E2E LTDA");
    await page.locator("#nome").fill("Tester");
    await page.locator("#email").fill("tester@empresa.com");
    await page.locator("#lgpd").check();
    await page.getByRole("button", { name: "Próxima Etapa" }).click();

    await page.locator("#cnae_principal").fill("1234567");
    await page.getByRole("button", { name: "Próxima Etapa" }).click();

    await expect(page.getByTestId("wizard-p8-normativa")).toBeVisible();
    await page
      .getByPlaceholder(/Ex\.:/)
      .fill("Conforme LC 214/2025 art. 5º o plano deve ser documentado.");

    await page.getByRole("button", { name: /Validar texto/i }).click();

    await expect(page.getByRole("status")).toContainText(/Aceito/i);
    expect(normativaHits).toBeGreaterThanOrEqual(1);

    await expect(page.getByTestId("wizard-pergunta-atual")).toBeVisible();
    await page.getByRole("radio", { name: /^Sim$/i }).first().check();
    await page.getByRole("button", { name: "Seguir" }).click();
    await expect(page.getByText(/Pergunta escala E2E/i)).toBeVisible();
    await page.getByRole("radio", { name: /^3$/ }).check();
    await page.getByRole("button", { name: /Finalizar Diagnóstico/i }).click();
    await page.waitForURL("**/sucesso**", { timeout: 15_000 });
  });
});
