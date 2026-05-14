import AxeBuilder from "@axe-core/playwright";
import { test, expect } from "@playwright/test";

/**
 * M1 — acessibilidade incremental: apenas violações `critical` em páginas críticas.
 * Não substitui auditoria manual; expandir regras gradualmente.
 */
/** `/dashboard` exige cookie de sessão painel — páginas públicas + login/cadastro cobrem o gate incremental M1. */
const urls = ["/", "/wizard", "/metodologia", "/login", "/cadastro"];

test.describe("Acessibilidade (axe — critical apenas)", () => {
  for (const path of urls) {
    test(`sem violações critical em ${path}`, async ({ page }) => {
      await page.goto(path);
      const results = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa"]).analyze();
      const critical = results.violations.filter((v) => v.impact === "critical");
      expect(critical, JSON.stringify(critical, null, 2)).toEqual([]);
    });
  }
});
