import { expect, test } from "@playwright/test";

const DIAG_ID = "44444444-4444-4444-a444-444444444444";
const LEITURA_TOKEN = "e2e-leitura-token-conclusao-explic-smoke-32ch";

const conclusaoBody = {
  id: DIAG_ID,
  status: "finalizado",
  empresa_razao_social: "Empresa E2E Conclusão",
  locale_relatorio: "pt-BR",
  score_geral: 61.5,
  scores_por_dimensao: [
    { dimensao: "fiscal", valor: 45.0, peso_total_aplicado: 1.5 },
    { dimensao: "tecnologica", valor: 72.0, peso_total_aplicado: 1.3 },
  ],
  explicacao_score_llm_texto:
    "Priorize governança fiscal antes da transição CBS/IBS (LC 214/2025).",
};

test.describe("Self-service — conclusão com explicação LLM", () => {
  test("exibe narrativa quando API devolve explicacao_score_llm_texto", async ({ page }) => {
    await page.route("**/diagnosticos/self-service/conclusao-visualizacao**", async (route) => {
      if (route.request().method() !== "GET") {
        await route.continue();
        return;
      }
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(conclusaoBody),
      });
    });

    const qs = new URLSearchParams({
      diagnostico_id: DIAG_ID,
      leitura_token: LEITURA_TOKEN,
    });
    await page.goto(`/diagnostico/concluido-self-service?${qs.toString()}`);

    await expect(page.getByRole("heading", { name: /Diagnóstico concluído/i })).toBeVisible();
    await expect(page.getByText("Explicação do score (IA)")).toBeVisible();
    await expect(page.getByText(/Priorize governança fiscal/)).toBeVisible();
    await expect(page.getByText(/61\.5 \/ 100/)).toBeVisible();
  });

  test("não exibe bloco IA quando texto ausente", async ({ page }) => {
    await page.route("**/diagnosticos/self-service/conclusao-visualizacao**", async (route) => {
      const { explicacao_score_llm_texto: _, ...semIa } = conclusaoBody;
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ ...semIa, explicacao_score_llm_texto: null }),
      });
    });

    const qs = new URLSearchParams({
      diagnostico_id: DIAG_ID,
      leitura_token: LEITURA_TOKEN,
    });
    await page.goto(`/diagnostico/concluido-self-service?${qs.toString()}`);

    await expect(page.getByRole("heading", { name: /Diagnóstico concluído/i })).toBeVisible();
    await expect(page.getByText("Explicação do score (IA)")).not.toBeVisible();
  });
});
