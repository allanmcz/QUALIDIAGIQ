import type { Page, Route } from "@playwright/test";

/** Alinhado a `frontend/lib/auth/painel_access_cookie.ts` — evitar import `@/` no runner E2E. */
const PAINEL_ACCESS_COOKIE = "qdi_painel_access";

function extrairEmailDoPost(route: Route, fallback: string): string {
  try {
    const body = route.request().postDataJSON() as { email?: string } | null;
    const e = body?.email;
    if (typeof e === "string" && e.trim()) return e.trim();
  } catch {
    /* corpo vazio ou não-JSON */
  }
  return fallback;
}

function extrairNomeEmailCadastro(route: Route, fallbacks: { nome: string; email: string }) {
  try {
    const body = route.request().postDataJSON() as { email?: string; nome?: string } | null;
    const email =
      typeof body?.email === "string" && body.email.trim() ? body.email.trim() : fallbacks.email;
    const nome =
      typeof body?.nome === "string" && body.nome.trim() ? body.nome.trim() : fallbacks.nome;
    return { nome, email };
  } catch {
    return fallbacks;
  }
}

async function fulfillBffPainelJson(
  route: Route,
  input: {
    tokenCookie: string;
    nome: string;
    email: string;
    perfil_conta: "gratuito" | "avancado";
  },
): Promise<void> {
  const cookieVal = encodeURIComponent(input.tokenCookie);
  await route.fulfill({
    status: 200,
    contentType: "application/json",
    headers: {
      "Set-Cookie": `${PAINEL_ACCESS_COOKIE}=${cookieVal}; Path=/; HttpOnly; SameSite=Lax; Max-Age=3600`,
    },
    body: JSON.stringify({
      ok: true,
      nome: input.nome,
      email: input.email,
      perfil_conta: input.perfil_conta,
    }),
  });
}

export type MockBffPainelAuthOpts = {
  /** Valor gravado no cookie httpOnly — o proxy `/api-backend` repassa como `Authorization: Bearer …`. */
  tokenParaUpstream?: string;
  nome?: string;
  perfil_conta?: "gratuito" | "avancado";
};

/**
 * Mock de `POST …/api/auth/login` (contrato BFF + cookie para same-origin com `NEXT_PUBLIC_API_URL=/api-backend`).
 */
export async function installMockBffPainelLogin(
  page: Page,
  opts: MockBffPainelAuthOpts = {},
): Promise<void> {
  const token = opts.tokenParaUpstream ?? "e2e-mock-jwt";
  const nome = opts.nome ?? "Consultor QA";
  const perfil = opts.perfil_conta ?? "gratuito";

  await page.route("**/api/auth/login", async (route) => {
    if (route.request().method() !== "POST") {
      await route.continue();
      return;
    }
    const email = extrairEmailDoPost(route, "e2e@teste.com");
    await fulfillBffPainelJson(route, { tokenCookie: token, nome, email, perfil_conta: perfil });
  });
}

/**
 * Mock de `POST …/api/auth/cadastro` — mesma política de cookie que o login BFF.
 */
export async function installMockBffPainelCadastro(
  page: Page,
  opts: MockBffPainelAuthOpts = {},
): Promise<void> {
  const token = opts.tokenParaUpstream ?? "e2e-mock-jwt-cadastro";
  const nomeDefault = opts.nome ?? "Novo Consultor E2E";
  const perfil = opts.perfil_conta ?? "gratuito";

  await page.route("**/api/auth/cadastro", async (route) => {
    if (route.request().method() !== "POST") {
      await route.continue();
      return;
    }
    const { nome, email } = extrairNomeEmailCadastro(route, {
      nome: nomeDefault,
      email: "novo.e2e@teste.com",
    });
    await fulfillBffPainelJson(route, { tokenCookie: token, nome, email, perfil_conta: perfil });
  });
}
