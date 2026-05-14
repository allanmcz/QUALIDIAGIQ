import { test, expect } from "@playwright/test";

import { installMockBffPainelLogin } from "./helpers/mock_bff_painel_auth";
import { fillWizardCnpjPasso1 } from "./helpers/wizard_cnpj_e2e";

/**
 * N3 — intercepta chamadas à API (sem Docker obrigatório).
 * Falha se o front alterar paths ou deixar de enviar POST /diagnosticos/.
 */
const PID_TERNARIA = "cafe0001-0001-4001-8001-000000000001";
const PID_ESCALA = "cafe0002-0002-4002-8002-000000000002";

test.describe("Wizard envia diagnóstico (mock API)", () => {
  test("login, wizard e POST com cookie BFF ou Bearer + Idempotency-Key", async ({ page }) => {
    test.setTimeout(90_000);
    const headersCapturados: { authorization?: string; idempotency?: string; cookie?: string } = {};

    await installMockBffPainelLogin(page, {
      tokenParaUpstream: "e2e-token-playwright",
      nome: "Usuário E2E",
    });

    let postJson = "";

    /** Um único handler evita cadeias `fallback()` entre globs e predicados (Playwright). */
    await page.route((url) => url.pathname.includes("/diagnosticos"), async (route) => {
      const u = route.request().url();
      const method = route.request().method();

      if (method === "GET" && u.includes("questionario")) {
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
        return;
      }

      if (method === "POST" && !u.includes("questionario") && !u.includes("metodologia")) {
        const h = route.request().headers();
        headersCapturados.authorization = h["authorization"] ?? h["Authorization"];
        headersCapturados.idempotency = h["idempotency-key"] ?? h["Idempotency-Key"];
        headersCapturados.cookie = h["cookie"] ?? h["Cookie"];
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
        return;
      }

      await route.continue();
    });

    await page.goto("/login");
    await page.getByLabel(/E-mail Corporativo/i).fill("e2e@teste.com");
    await page.locator("#password").fill("qualquer");
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

    await expect(page.locator("#cnpj")).toBeVisible();
    await fillWizardCnpjPasso1(page);
    await page.locator("#razao_social").fill("Empresa E2E LTDA");
    await page.locator("#nome").fill("Tester");
    await page.locator("#email").fill("tester@empresa.com");
    await page.locator("#lgpd").check();
    await page.getByRole("button", { name: "Próxima Etapa" }).click();

    await page.locator("#porte").selectOption("micro");
    await page.locator("#regime").selectOption("simples_nacional");
    await page.locator("#setor_macro").selectOption("comercio");
    await page.locator("#uf").selectOption("SP");
    await page.locator("#cnae_principal").fill("1234567");
    await page.getByRole("button", { name: "Próxima Etapa" }).click();

    await expect(page.getByTestId("wizard-pergunta-atual")).toBeVisible();
    await expect(page.getByText(/Pergunta ternária E2E/i)).toBeVisible();
    await page.getByRole("radio", { name: /^Sim$/i }).first().check();
    await page.getByRole("button", { name: "Seguir" }).click();

    await expect(page.getByText(/Pergunta escala E2E/i)).toBeVisible();
    await page
      .getByTestId("wizard-pergunta-atual")
      .locator('input[type="radio"][value="3"]')
      .check();
    await page.getByRole("button", { name: /Finalizar Diagnóstico/i }).click();

    await page.waitForURL("**/sucesso**", { timeout: 15_000 });

    const auth = headersCapturados.authorization || "";
    const cookie = headersCapturados.cookie || "";
    expect(
      auth.includes("Bearer e2e-token-playwright") ||
        cookie.includes("qdi_painel_access=e2e-token-playwright"),
    ).toBe(true);
    expect(headersCapturados.idempotency || "").toMatch(/[0-9a-f-]{36}/i);
    expect(postJson).toContain(PID_TERNARIA);
    expect(postJson).toContain(PID_ESCALA);
    const posted = JSON.parse(postJson) as { aceite_termos_privacidade?: boolean; plano?: string };
    expect(posted.aceite_termos_privacidade).toBe(true);
    expect(posted.plano).toBe("gratuito");
  });
});
