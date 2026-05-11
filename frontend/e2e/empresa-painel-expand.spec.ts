import type { Page } from "@playwright/test";
import { expect, test } from "@playwright/test";

/** Smoke handoff P3 — grelha empresa + expandir (API mockada; sem backend real). */
const DIAG_ID = "22222222-2222-4222-a222-222222222222";
const CNPJ14 = "12345678000195";

function buildAbnt10Acoes() {
  return Array.from({ length: 10 }, (_, i) => ({
    descricao: `Controle ABNT M12 #${i + 1} (E2E)`,
    responsavel: "QA",
    prazo: "—",
    criticidade: "Média",
    prioridade: i + 1,
  }));
}

const listaItem = {
  id: DIAG_ID,
  empresa_razao_social: "Empresa E2E Painel Empresa",
  empresa_cnpj: CNPJ14,
  status: "finalizado",
  plano: "gratuito",
  score_geral: 52,
  criado_em: "2026-05-11T10:00:00Z",
  finalizado_em: "2026-05-11T10:30:00Z",
  relatorio_pdf_url: null,
};

const detalheBody = {
  id: DIAG_ID,
  empresa_razao_social: listaItem.empresa_razao_social,
  empresa_cnpj: CNPJ14,
  status: "finalizado",
  plano: "gratuito",
  versao_otimista: 1,
  relatorio_pdf_url: null,
  checklist_m12_autoconf: null,
  quadro_implantacao_anotacoes: null,
  matriz_impacto: [],
  cronograma: [],
  score: {
    score_geral: { valor: 52 },
    score_por_dimensao: {
      fiscal: { valor: 42, peso_total_aplicado: 1.5 },
      tecnologica: { valor: 62, peso_total_aplicado: 1.3 },
    },
  },
  checklist: [
    {
      nome: "ABNT NBR 17301 — 10 controlos M12",
      acoes: buildAbnt10Acoes(),
    },
  ],
};

/**
 * Mocks partilhados: login, lista/detalhe diagnósticos, retificações (lista vazia),
 * solicitações LGPD (lista vazia — card «Nenhuma solicitação…»).
 */
async function installPainelEmpresaApiMocks(page: Page): Promise<void> {
  await page.route("**/auth/login", async (route) => {
    if (route.request().method() !== "POST") {
      await route.continue();
      return;
    }
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        access_token: "e2e-empresa-token",
        nome: "Consultor QA",
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
      body: JSON.stringify([]),
    });
  });

  await page.route("**/diagnosticos/**", async (route) => {
    if (route.request().method() !== "GET") {
      await route.continue();
      return;
    }
    const pathname = new URL(route.request().url()).pathname.replace(/\/$/, "");
    // Não interceptar UI `/dashboard/diagnosticos/...` — glob `diagnosticos` apanha também o fetch RSC do Next.
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
    if (rest.length === 0) {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([listaItem]),
      });
      return;
    }
    if (rest.length >= 2 && rest[rest.length - 1] === "retificacoes") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([]),
      });
      return;
    }
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(detalheBody),
    });
  });
}

async function loginPainelE2E(page: Page): Promise<void> {
  await page.goto("/login");
  await page.getByLabel(/E-mail Corporativo/i).fill("consultor@teste.com.br");
  await page.getByLabel(/^Senha$/i).fill("qualquer-senha");
  await page.getByRole("button", { name: /Entrar no Dashboard/i }).click();
}

test.describe("Painel empresa — expandir linha", () => {
  test("expandir mostra ranking ou radar (mock)", async ({ page }) => {
    await installPainelEmpresaApiMocks(page);
    await loginPainelE2E(page);

    await page.goto(`/dashboard/empresas/${CNPJ14}`);
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();

    await page.getByRole("button", { name: /Expandir/i }).click();

    await expect(
      page.getByRole("heading", { name: /Ranking explícito de gaps — este diagnóstico/i }),
    ).toBeVisible({ timeout: 15_000 });
  });

  test("atalho LGPD deste diagnóstico abre ficha com âncora (mock)", async ({ page }) => {
    await installPainelEmpresaApiMocks(page);
    await loginPainelE2E(page);

    await page.goto(`/dashboard/empresas/${CNPJ14}`);
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();

    await page.getByRole("button", { name: /Expandir/i }).click();
    await expect(
      page.getByRole("heading", { name: /Ranking explícito de gaps — este diagnóstico/i }),
    ).toBeVisible({ timeout: 15_000 });

    await page.getByRole("link", { name: /LGPD deste diagnóstico/i }).click();

    await expect(page).toHaveURL(new RegExp(`/dashboard/diagnosticos/${DIAG_ID}`));
    const cardLgpd = page.locator("#diag-privacidade-lgpd");
    await expect(cardLgpd).toBeVisible({ timeout: 15_000 });
    await expect(cardLgpd.getByText(/Privacidade LGPD \(este diagnóstico\)/i)).toBeVisible();
  });
});
