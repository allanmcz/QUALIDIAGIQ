import { test, expect } from "@playwright/test";

/**
 * ADR-012 §4 — smoke do painel: solicitação portabilidade deferida → GET export mockado → mensagem de sucesso.
 * Sem API real (mesmo padrão de `dashboard-list.spec.ts`).
 */
test.describe("Dashboard privacidade — export portabilidade (mock API)", () => {
  const diagnosticoId = "22222222-2222-4222-a222-222222222222";
  const solicitacaoId = "33333333-3333-4333-a333-333333333333";

  test("lista pedido deferido e descarga JSON dispara mensagem de sucesso", async ({ page }) => {
    await page.route("**/auth/login", async (route) => {
      if (route.request().method() !== "POST") {
        await route.continue();
        return;
      }
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          access_token: "e2e-privacidade-token",
          nome: "Consultor LGPD E2E",
          perfil_conta: "gratuito",
        }),
      });
    });

    await page.route("**/privacidade/solicitacoes**", async (route) => {
      if (route.request().method() !== "GET") {
        await route.continue();
        return;
      }
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([
          {
            id: solicitacaoId,
            tenant_id: "44444444-4444-4444-a444-444444444444",
            diagnostico_id: diagnosticoId,
            tipo: "portabilidade",
            status: "deferida",
            canal: "plataforma",
            solicitante_email: "titular@e2e.example",
            payload: {},
            observacao_interna: null,
            actor_user_id: null,
            criado_em: "2026-05-09T10:00:00Z",
            atualizado_em: "2026-05-09T10:00:00Z",
          },
        ]),
      });
    });

    const exportBody = JSON.stringify({ schema_id: "qdi-diagnostico-export-v1" });
    await page.route("**/privacidade/diagnosticos/**/export-portabilidade**", async (route) => {
      if (route.request().method() !== "GET") {
        await route.continue();
        return;
      }
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: exportBody,
      });
    });

    await page.goto("/login");
    await page.getByLabel(/E-mail Corporativo/i).fill("consultor@teste.com.br");
    await page.getByLabel(/^Senha$/i).fill("qualquer-senha");
    await page.getByRole("button", { name: /Entrar no Dashboard/i }).click();

    await page.goto("/dashboard/privacidade");
    await expect(page.getByRole("heading", { name: /Privacidade LGPD/i })).toBeVisible();
    await expect(page.getByText("titular@e2e.example")).toBeVisible();

    await page.getByRole("button", { name: "JSON" }).click();
    await expect(page.getByRole("status")).toContainText(/Export JSON descarregado/i);
  });
});
