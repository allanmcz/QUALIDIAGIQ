import { expect, test } from "@playwright/test";

import { installMockBffPainelLogin } from "./helpers/mock_bff_painel_auth";
import { installMockListaDiagnosticosPorEmpresa } from "./helpers/mock_diagnosticos_lista_por_empresa";

const CNPJ14 = "11222333000181";
const RAZAO = "Empresa E2E Novo Ciclo SA";

const listaDoisCiclos = [
  {
    id: "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
    empresa_razao_social: RAZAO,
    empresa_cnpj: CNPJ14,
    status: "finalizado",
    plano: "gratuito",
    score_geral: 55,
    criado_em: "2026-05-01T10:00:00Z",
    finalizado_em: "2026-05-01T11:00:00Z",
    relatorio_pdf_url: null,
    numero_interno_grupo: 1,
  },
  {
    id: "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
    empresa_razao_social: RAZAO,
    empresa_cnpj: CNPJ14,
    status: "em_andamento",
    plano: "gratuito",
    score_geral: null,
    criado_em: "2026-05-10T10:00:00Z",
    finalizado_em: null,
    relatorio_pdf_url: null,
    numero_interno_grupo: 2,
  },
];

async function dispensarOverlayRascunho(page: import("@playwright/test").Page) {
  const dialog = page.getByRole("dialog", {
    name: /Diagnóstico em andamento neste navegador/i,
  });
  if (await dialog.isVisible()) {
    await dialog.getByRole("button", { name: /Reiniciar diagnóstico/i }).click();
  }
}

async function aguardarHistoricoEmpresaMock(page: import("@playwright/test").Page) {
  await page.waitForResponse(
    (res) => {
      if (res.request().method() !== "GET") return false;
      const u = new URL(res.url());
      if (!u.pathname.includes("diagnosticos")) return false;
      return u.searchParams.get("empresa_cnpj")?.replace(/\D/g, "") === CNPJ14;
    },
    { timeout: 15_000 },
  );
}

async function instalarSessaoEMocks(page: import("@playwright/test").Page) {
  await installMockBffPainelLogin(page, {
    tokenParaUpstream: "e2e-wizard-novo-ciclo",
    nome: "QA E2E Novo Ciclo",
    limparLocalStoragePainelAntesDeCadaDocumento: true,
  });
  await installMockListaDiagnosticosPorEmpresa(page, CNPJ14, listaDoisCiclos);

  await page.addInitScript(() => {
    window.localStorage.removeItem("qdi_wizard_draft_v1");
    window.localStorage.setItem("admin_perfil_conta", "gratuito");
    window.localStorage.setItem("admin_nome", "QA E2E Novo Ciclo");
    window.localStorage.setItem("admin_email", "qa.novo.ciclo@example.com");
  });
}

function urlWizardNovoCiclo(): string {
  const qs = new URLSearchParams({
    modo: "novo_ciclo",
    empresa_cnpj: CNPJ14,
    empresa_razao_social: RAZAO,
  });
  return `/wizard?${qs.toString()}`;
}

test.describe("Wizard — novo ciclo (empresa já no painel)", () => {
  test("passo 1 com modo=novo_ciclo mostra banner e título de novo ciclo", async ({ page }) => {
    await instalarSessaoEMocks(page);

    const historico = aguardarHistoricoEmpresaMock(page);
    await page.goto(urlWizardNovoCiclo());

    await dispensarOverlayRascunho(page);
    await historico;

    await expect(page.getByText(`Novo ciclo — ${RAZAO}`)).toBeVisible();

    await expect(page.getByText(/Empresa já cadastrada no painel/i).first()).toBeVisible({
      timeout: 15_000,
    });
    await expect(page.getByText(/2 diagnósticos anteriores/i).first()).toBeVisible();
    await expect(page.getByText(/ciclo nº 3/i).first()).toBeVisible();
    await expect(page.getByText(/não é um novo cadastro de empresa/i).first()).toBeVisible();
  });

  test("passo 2 mantém aviso de novo ciclo após Próxima Etapa", async ({ page }) => {
    await instalarSessaoEMocks(page);

    const historico = aguardarHistoricoEmpresaMock(page);
    await page.goto(urlWizardNovoCiclo());

    await dispensarOverlayRascunho(page);
    await historico;

    await expect(page.getByText(/Empresa já cadastrada no painel/i).first()).toBeVisible({
      timeout: 15_000,
    });

    await page.getByLabel(/Seu Nome \*/i).fill("Fulano QA");
    await page.getByLabel(/E-mail Profissional \*/i).fill("qa.novo.ciclo@example.com");
    await page.getByRole("checkbox", { name: /Declaro que li e aceito/i }).check();

    await page.getByRole("button", { name: "Próxima Etapa" }).click();

    await expect(page.getByText("Perfil da empresa (novo ciclo)")).toBeVisible();
    await expect(page.getByText(/ciclo nº 3/i).first()).toBeVisible();
  });

  test("mock lista por CNPJ responde com histórico (sanidade do helper)", async ({ page }) => {
    await instalarSessaoEMocks(page);

    await page.goto(urlWizardNovoCiclo());
    await dispensarOverlayRascunho(page);

    const status = await page.evaluate(async (cnpj) => {
      const res = await fetch(
        `/api-backend/diagnosticos?limit=100&offset=0&empresa_cnpj=${encodeURIComponent(cnpj)}`,
        { credentials: "include" },
      );
      const body = (await res.json()) as unknown[];
      return { ok: res.ok, len: Array.isArray(body) ? body.length : 0 };
    }, CNPJ14);

    expect(status.ok).toBe(true);
    expect(status.len).toBe(2);
  });
});
