import type { Page } from "@playwright/test";

/**
 * Mock de `GET …/diagnosticos` (lista resumo) — mesmo padrão de `e2e/dashboard-list.spec.ts`.
 * Útil após login/cadastro BFF quando não há API real no `API_PROXY_TARGET`.
 */
export async function installMockListaDiagnosticosGet(
  page: Page,
  corpo: unknown = [],
): Promise<void> {
  await page.route("**/diagnosticos/**", async (route) => {
    if (route.request().method() !== "GET") {
      await route.continue();
      return;
    }
    const path = new URL(route.request().url()).pathname.replace(/\/$/, "");
    if (!path.endsWith("/diagnosticos")) {
      await route.continue();
      return;
    }
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(corpo),
    });
  });
}
