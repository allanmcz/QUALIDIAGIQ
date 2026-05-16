import type { Page } from "@playwright/test";

import { painelInterceptarUrlApiDiagnosticos } from "./painel_api_diagnosticos_url";

/**
 * Mock de `GET …/diagnosticos?empresa_cnpj=` — lista por PJ para E2E wizard «novo ciclo».
 */
export async function installMockListaDiagnosticosPorEmpresa(
  page: Page,
  cnpj14: string,
  corpo: unknown,
): Promise<void> {
  const alvo = cnpj14.replace(/\D/g, "");
  await page.route(painelInterceptarUrlApiDiagnosticos, async (route) => {
    if (route.request().method() !== "GET") {
      await route.continue();
      return;
    }
    const url = new URL(route.request().url());
    const pathname = url.pathname.replace(/\/$/, "");
    if (pathname.includes("/dashboard/diagnosticos")) {
      await route.continue();
      return;
    }
    const parts = pathname.split("/").filter(Boolean);
    const di = parts.lastIndexOf("diagnosticos");
    if (di === -1) {
      await route.continue();
      return;
    }
    const rest = parts.slice(di + 1);
    if (rest.length > 0) {
      await route.continue();
      return;
    }

    const filtro = url.searchParams.get("empresa_cnpj")?.replace(/\D/g, "") ?? "";
    if (filtro === alvo) {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(corpo),
      });
      return;
    }
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify([]),
    });
  });
}
