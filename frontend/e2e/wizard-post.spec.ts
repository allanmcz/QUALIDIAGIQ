import { test, expect } from "@playwright/test";

/**
 * N3 — intercepta chamadas à API (sem Docker obrigatório).
 * Falha se o front alterar paths ou deixar de enviar POST /diagnosticos/.
 */
const PID_TERNARIA = "cafe0001-0001-4001-8001-000000000001";
const PID_ESCALA = "cafe0002-0002-4002-8002-000000000002";

test.describe("Wizard envia diagnóstico (mock API)", () => {
  test("login, wizard e POST com Bearer + Idempotency-Key", async ({ page }) => {
    test.setTimeout(60_000);
    const headersCapturados: { authorization?: string; idempotency?: string } = {};

    await page.route("**/auth/login", async (route) => {
      if (route.request().method() !== "POST") {
        await route.continue();
        return;
      }
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          access_token: "e2e-token-playwright",
          nome: "Usuário E2E",
        }),
      });
    });

    let postJson = "";

    /** Rotas mais específicas devem ser registradas por último (Playwright avalia da última para a primeira). */
    await page.route("**/diagnosticos**", async (route) => {
      const u = route.request().url();
      if (
        route.request().method() !== "POST" ||
        u.includes("questionario") ||
        u.includes("metodologia")
      ) {
        await route.continue();
        return;
      }
      const h = route.request().headers();
      headersCapturados.authorization = h["authorization"] ?? h["Authorization"];
      headersCapturados.idempotency = h["idempotency-key"] ?? h["Idempotency-Key"];
      postJson = route.request().postData() || "";
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
            score_por_dimensao: {
              fiscal: { valor: 80, peso_total_aplicado: 1 },
            },
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
          versao_catalogo: "e2e-mock",
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

    await expect(page.getByText(/Pergunta ternária E2E/i)).toBeVisible();
    await page.getByRole("radio", { name: /^Sim$/i }).first().check();
    await page.getByRole("radio", { name: /3 - escala/i }).check();

    await page.getByRole("button", { name: /Finalizar Diagnóstico/i }).click();

    await page.waitForURL("**/sucesso**", { timeout: 15_000 });

    expect(headersCapturados.authorization || "").toContain("Bearer e2e-token-playwright");
    expect(headersCapturados.idempotency || "").toMatch(/[0-9a-f-]{36}/i);
    expect(postJson).toContain(PID_TERNARIA);
    expect(postJson).toContain(PID_ESCALA);
    const posted = JSON.parse(postJson) as { aceite_termos_privacidade?: boolean };
    expect(posted.aceite_termos_privacidade).toBe(true);
  });
});
