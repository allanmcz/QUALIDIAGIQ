import { test, expect } from "@playwright/test";

/** Alinhado a `frontend/lib/wizard/wizard_draft.ts` — evitar import para o runner E2E não depender de bundle. */
const STORAGE_WIZARD_DRAFT = "qdi_wizard_draft_v1";
/** Alinhado a `frontend/lib/wizard/pending_diagnostico.ts`. */
const STORAGE_PENDING_DIAGNOSTICO = "qdi_pending_post_diagnostico_v1";

/** Rascunho mínimo com progresso (`step >= 2` ⇒ `wizardDraftHasProgress`). */
const draftComProgresso = {
  v: 1 as const,
  step: 2,
  indicePerguntaAtual: 0,
  form: {
    empresa: {
      cnpj: "",
      razao_social: "",
      porte: "",
      regime: "",
      cnae_principal: "",
      uf: "",
      setor_macro: "",
    },
    respondente: { nome: "", email: "", telefone: "" },
    locale_relatorio: "pt-BR",
    plano: "gratuito",
    respostas: [] as unknown[],
    aceite_termos_privacidade: false,
  },
};

/** Payload válido para `DiagnosticoPayloadArmazenadoSchema.safeParse` (pendente pós-wizard). */
const pendingDiagnosticoValido = {
  empresa: {
    cnpj: "12345678000195",
    razao_social: "Empresa E2E LTDA",
    porte: "medio",
    regime: "lucro_real",
    cnae_principal: "6201500",
    uf: "SP",
    setor_macro: "servicos",
  },
  respondente: {
    nome: "Fulano E2E",
    email: "fulano.e2e@example.com",
  },
  respostas: [{ pergunta_id: "f47ac10b-58cc-4372-a567-0e02b2c3d479", valor: "sim" }],
  plano: "gratuito",
  locale_relatorio: "pt-BR",
  aceite_termos_privacidade: true,
};

test.describe("Wizard — retomada de cache (localStorage)", () => {
  test("com rascunho: exibe diálogo com copy e botões Continuar / Reiniciar", async ({ page }) => {
    await page.addInitScript((payload: { key: string; value: string }) => {
      window.localStorage.setItem(payload.key, payload.value);
    }, { key: STORAGE_WIZARD_DRAFT, value: JSON.stringify(draftComProgresso) });

    await page.goto("/wizard");

    const dialog = page.getByRole("dialog", {
      name: /Diagnóstico em andamento neste navegador/i,
    });
    await expect(dialog).toBeVisible();

    await expect(
      dialog.getByText(/Há dados do assistente em cache local neste navegador/i),
    ).toBeVisible();
    await expect(dialog.getByText(/Rascunho do wizard/i)).toBeVisible();
    await expect(dialog.getByRole("button", { name: /^Continuar$/ })).toBeVisible();
    await expect(dialog.getByRole("button", { name: /Reiniciar diagnóstico/i })).toBeVisible();
  });

  test("com diagnóstico pendente: lista conclusão aguardando login", async ({ page }) => {
    await page.addInitScript((payload: { key: string; value: string }) => {
      window.localStorage.setItem(payload.key, payload.value);
    }, {
      key: STORAGE_PENDING_DIAGNOSTICO,
      value: JSON.stringify(pendingDiagnosticoValido),
    });

    await page.goto("/wizard");

    const dialog = page.getByRole("dialog", {
      name: /Diagnóstico em andamento neste navegador/i,
    });
    await expect(dialog).toBeVisible();
    await expect(
      dialog.getByText(/Rascunho legado no navegador ou fluxo de confirmação/i),
    ).toBeVisible();
    await expect(dialog.getByText(/LGPD: trata-se de cache local/i)).toBeVisible();
  });

  test("com rascunho e pendente: exibe ambos os itens e nota de «Continuar»", async ({ page }) => {
    await page.addInitScript((payload: { draft: string; pending: string }) => {
      window.localStorage.setItem("qdi_wizard_draft_v1", payload.draft);
      window.localStorage.setItem("qdi_pending_post_diagnostico_v1", payload.pending);
    }, {
      draft: JSON.stringify(draftComProgresso),
      pending: JSON.stringify(pendingDiagnosticoValido),
    });

    await page.goto("/wizard");

    const dialog = page.getByRole("dialog", {
      name: /Diagnóstico em andamento neste navegador/i,
    });
    await expect(dialog).toBeVisible();
    await expect(dialog.getByText(/Rascunho do wizard/i)).toBeVisible();
    await expect(
      dialog.getByText(/Rascunho legado no navegador ou fluxo de confirmação/i),
    ).toBeVisible();
    await expect(
      dialog.getByText(/«Continuar» restaura o rascunho do assistente/i),
    ).toBeVisible();
  });

  test("Reiniciar diagnóstico fecha o diálogo e remove o rascunho do localStorage", async ({
    page,
  }) => {
    await page.addInitScript((payload: { key: string; value: string }) => {
      window.localStorage.setItem(payload.key, payload.value);
    }, { key: STORAGE_WIZARD_DRAFT, value: JSON.stringify(draftComProgresso) });

    await page.goto("/wizard");

    const dialog = page.getByRole("dialog", {
      name: /Diagnóstico em andamento neste navegador/i,
    });
    await expect(dialog).toBeVisible();

    await dialog.getByRole("button", { name: /Reiniciar diagnóstico/i }).click();

    await expect(dialog).toBeHidden();
    const draftRestante = await page.evaluate((k) => window.localStorage.getItem(k), STORAGE_WIZARD_DRAFT);
    expect(draftRestante).toBeNull();
  });

  test("modo=nova_empresa (painel): não exibe diálogo e limpa rascunho local", async ({ page }) => {
    await page.addInitScript((payload: { key: string; value: string }) => {
      window.localStorage.setItem(payload.key, payload.value);
    }, { key: STORAGE_WIZARD_DRAFT, value: JSON.stringify(draftComProgresso) });

    await page.goto("/wizard?modo=nova_empresa");

    const dialog = page.getByRole("dialog", {
      name: /Diagnóstico em andamento neste navegador/i,
    });
    await expect(dialog).toBeHidden();

    const draftRestante = await page.evaluate((k) => window.localStorage.getItem(k), STORAGE_WIZARD_DRAFT);
    expect(draftRestante).toBeNull();
  });
});
