import { test, expect } from "@playwright/test";

import { installMockBffPainelLogin } from "./helpers/mock_bff_painel_auth";

/**
 * A1 — edge cases do wizard: multipla_total, opções vazias (rótulos genéricos), voltar entre passos.
 * Mock da API — não exige Docker.
 */
const PID_T = "cafe0010-0010-4010-8010-000000000010";
const PID_M = "cafe0011-0011-4011-8011-000000000011";

test.describe("Wizard — edge cases (mock API)", () => {
  test.beforeEach(async ({ page }) => {
    await installMockBffPainelLogin(page, {
      tokenParaUpstream: "e2e-edge-token",
      nome: "E2E Edge",
    });

    await page.route(
      (url) => url.pathname.includes("/diagnosticos/questionario"),
      async (route) => {
        if (route.request().method() !== "GET") {
          await route.fallback();
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
      },
    );

    await page.route("**/diagnosticos**", async (route) => {
      const u = route.request().url();
      if (
        route.request().method() !== "POST" ||
        u.includes("questionario") ||
        u.includes("metodologia")
      ) {
        await route.fallback();
        return;
      }
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
    });
  });

  test("opções vazias exibe aviso e permite concluir com Opção 1/2", async ({ page }) => {
    test.setTimeout(60_000);

    await page.goto("/login");
    await page.getByLabel(/E-mail Corporativo/i).fill("edge@teste.com");
    await page.locator("#password").fill("x");
    await page.getByRole("button", { name: /Entrar no Dashboard/i }).click();
    await page.waitForURL("**/dashboard**", { timeout: 15_000 });

    await page.evaluate(() => {
      try {
        window.localStorage.removeItem("qdi_wizard_draft_v1");
        window.localStorage.removeItem("qdi_pending_post_diagnostico_v1");
        window.localStorage.removeItem("qdi_rascunho_resgate_token_v1");
      } catch {
        /* ignore */
      }
    });

    await page.goto("/wizard");

    const dialogoRetoma = page.getByRole("dialog", { name: /Diagnóstico em andamento neste navegador/i });
    if (await dialogoRetoma.isVisible().catch(() => false)) {
      await dialogoRetoma.getByRole("button", { name: /Reiniciar diagnóstico/i }).click();
    }

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

test.describe("Wizard — catálogo multipla inválido (mock API)", () => {
  test.beforeEach(async ({ page }) => {
    await page.route("**/diagnosticos/questionario*", async (route) => {
      if (route.request().method() !== "GET") {
        await route.continue();
        return;
      }
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          versao_catalogo: "e2e-invalid",
          total: 2,
          perguntas: [
            {
              id: "cafe0010-0010-4010-8010-000000000010",
              codigo: "Q-E2E-T",
              texto: "Ternária",
              tipo: "ternaria",
              peso: 1,
              dimensao: "fiscal",
              base_legal: null,
              multipla_total: null,
              opcoes: null,
            },
            {
              id: "cafe0012-0012-4012-8012-000000000012",
              codigo: "Q-E2E-BAD",
              texto: "Múltipla sem total",
              tipo: "multipla_escolha",
              peso: 1,
              dimensao: "fiscal",
              base_legal: null,
              multipla_total: null,
              opcoes: ["A", "B"],
            },
          ],
        }),
      });
    });
  });

  test("multipla_total ausente mostra erro de catálogo e não avança", async ({ page }) => {
    test.setTimeout(45_000);
    await page.goto("/wizard");
    await page.locator("#cnpj").fill("12345678000195");
    await page.locator("#razao_social").fill("Cat Inválida SA");
    await page.locator("#nome").fill("Tester");
    await page.locator("#email").fill("cat@empresa.com");
    await page.locator("#lgpd").check();
    await page.getByRole("button", { name: "Próxima Etapa" }).click();

    await page.locator("#porte").selectOption("micro");
    await page.locator("#regime").selectOption("simples_nacional");
    await page.locator("#setor_macro").selectOption("comercio");
    await page.locator("#uf").selectOption("SP");
    await page.locator("#cnae_principal").fill("1234567");
    await page.getByRole("button", { name: "Próxima Etapa" }).click();

    await page.getByRole("radio", { name: /^Sim$/i }).first().check();
    await page.getByRole("button", { name: "Seguir" }).click();

    await expect(page.getByText(/Catálogo incompleto/i)).toBeVisible();
    // Código da pergunta no título e possivelmente na mensagem — evitar strict mode (2 matches).
    await expect(page.getByText(/Q-E2E-BAD/).first()).toBeVisible();
  });
});
