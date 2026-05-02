import { test, expect } from "@playwright/test";

/**
 * A1 — edge cases do wizard: multipla_total, opções vazias (rótulos genéricos), voltar entre passos.
 * Mock da API — não exige Docker.
 */
const PID_T = "cafe0010-0010-4010-8010-000000000010";
const PID_M = "cafe0011-0011-4011-8011-000000000011";

test.describe("Wizard — edge cases (mock API)", () => {
  test.beforeEach(async ({ page }) => {
    await page.route("**/auth/login", async (route) => {
      if (route.request().method() !== "POST") {
        await route.continue();
        return;
      }
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          access_token: "e2e-edge-token",
          nome: "E2E Edge",
        }),
      });
    });

    await page.route("**/diagnosticos**", async (route) => {
      const u = route.request().url();
      if (route.request().method() === "POST" && !u.includes("questionario")) {
        await route.fulfill({
          status: 201,
          contentType: "application/json",
          body: JSON.stringify({
            id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            status: "finalizado",
            plano: "gratuito",
            empresa_razao_social: "Edge LTDA",
            score: {
              score_geral: { valor: 70, peso_total_aplicado: 1 },
              score_por_dimensao: { fiscal: { valor: 70, peso_total_aplicado: 1 } },
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
        return;
      }
      await route.continue();
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
          versao_catalogo: "e2e-edge",
          total: 2,
          perguntas: [
            {
              id: PID_T,
              codigo: "Q-E2E-T2",
              texto: "Pergunta ternária edge",
              tipo: "ternaria",
              peso: 1,
              dimensao: "fiscal",
              base_legal: null,
              multipla_total: null,
              opcoes: null,
            },
            {
              id: PID_M,
              codigo: "Q-E2E-M",
              texto: "Múltipla sem rótulos no catálogo",
              tipo: "multipla_escolha",
              peso: 1,
              dimensao: "fiscal",
              base_legal: null,
              multipla_total: 2,
              opcoes: [],
            },
          ],
        }),
      });
    });
  });

  test("opções vazias exibe aviso e permite concluir com Opção 1/2", async ({ page }) => {
    test.setTimeout(60_000);

    await page.goto("/login");
    await page.getByLabel(/E-mail Corporativo/i).fill("edge@teste.com");
    await page.locator("#password").fill("x");
    await page.getByRole("button", { name: /Entrar no Dashboard/i }).click();
    await page.waitForURL("**/dashboard**", { timeout: 15_000 });

    await page.goto("/wizard");

    await page.locator("#cnpj").fill("12345678000195");
    await page.locator("#razao_social").fill("Edge LTDA");
    await page.locator("#nome").fill("Edge");
    await page.locator("#email").fill("edge@empresa.com");
    await page.locator("#lgpd").check();
    await page.getByRole("button", { name: "Próxima Etapa" }).click();

    await page.locator("#porte").selectOption("micro");
    await page.locator("#regime").selectOption("simples_nacional");
    await page.locator("#setor_macro").selectOption("comercio");
    await page.locator("#uf").selectOption("SP");
    await page.locator("#cnae_principal").fill("1234567");
    await page.getByRole("button", { name: "Próxima Etapa" }).click();

    await expect(page.getByText(/Pergunta ternária edge/i)).toBeVisible();

    await page.getByRole("radio", { name: /^Sim$/i }).first().check();
    await page.getByRole("button", { name: "Seguir" }).click();

    await expect(page.getByText(/Múltipla sem rótulos/i)).toBeVisible();
    await expect(page.getByText(/catálogo não enviou rótulos/i)).toBeVisible();
    await page.getByRole("checkbox", { name: /Opção 1/i }).check();
    await page.getByRole("checkbox", { name: /Opção 2/i }).check();
    await page.getByRole("button", { name: /Finalizar Diagnóstico/i }).click();

    await page.waitForURL("**/sucesso**", { timeout: 15_000 });
  });

  test("transição Voltar entre passos 2 e 1 preserva fluxo", async ({ page }) => {
    test.setTimeout(45_000);

    await page.goto("/wizard");
    await page.locator("#cnpj").fill("12345678000195");
    await page.locator("#razao_social").fill("Volta SA");
    await page.locator("#nome").fill("User");
    await page.locator("#email").fill("v@empresa.com");
    await page.locator("#lgpd").check();
    await page.getByRole("button", { name: "Próxima Etapa" }).click();

    await expect(page.locator("#cnae_principal")).toBeVisible();
    await page.locator("#porte").selectOption("micro");
    await page.locator("#regime").selectOption("simples_nacional");
    await page.locator("#setor_macro").selectOption("comercio");
    await page.locator("#uf").selectOption("SP");
    await page.getByRole("button", { name: "Voltar" }).click();
    await expect(page.locator("#cnpj")).toBeVisible();
    await page.getByRole("button", { name: "Próxima Etapa" }).click();
    await page.locator("#porte").selectOption("micro");
    await page.locator("#regime").selectOption("simples_nacional");
    await page.locator("#setor_macro").selectOption("comercio");
    await page.locator("#uf").selectOption("SP");
    await page.locator("#cnae_principal").fill("1234567");
    await page.getByRole("button", { name: "Próxima Etapa" }).click();
    await expect(page.getByTestId("wizard-pergunta-atual")).toBeVisible({ timeout: 15_000 });
  });
});
