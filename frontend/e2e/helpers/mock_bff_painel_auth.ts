import type { Page, Route } from "@playwright/test";

/** Alinhado a `frontend/lib/auth/painel_access_cookie.ts` — evitar import `@/` no runner E2E. */
const PAINEL_ACCESS_COOKIE = "qdi_painel_access";

/** Só JWT legado — não apagar perfil/email/nome: o login BFF regrava antes do próximo GET e há full navigation nos E2E. */
const LS_JWT_LEGACY_PAINEL_LIMPAR_E2E = ["admin_token", "admin_token_expires_at"] as const;

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
    /** Segundos — sessões E2E longas (`--debug`, CI lento). */
    cookieMaxAgeSegundos?: number;
  },
): Promise<void> {
  const maxAge = input.cookieMaxAgeSegundos ?? 28_800;
  const cookieVal = encodeURIComponent(input.tokenCookie);
  await route.fulfill({
    status: 200,
    contentType: "application/json",
    headers: {
      "Set-Cookie": `${PAINEL_ACCESS_COOKIE}=${cookieVal}; Path=/; HttpOnly; SameSite=Lax; Max-Age=${maxAge}`,
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
  /** `Max-Age` do cookie mock (segundos). Omitir → 8h (evita expirar em depuração). */
  cookieMaxAgeSegundos?: number;
  /**
   * Antes de cada carregamento de documento, remove só `admin_token` (e expiração),
   * para não enviar Bearer legado inválido ao proxy. Mantém perfil/nome/email gravados pelo login BFF.
   */
  limparLocalStoragePainelAntesDeCadaDocumento?: boolean;
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
  const limparLs = opts.limparLocalStoragePainelAntesDeCadaDocumento ?? false;
  const cookieMaxAgeSegundos = opts.cookieMaxAgeSegundos;

  if (limparLs) {
    await page.addInitScript((keys: readonly string[]) => {
      try {
        for (const k of keys) window.localStorage.removeItem(k);
      } catch {
        /* storage indisponível */
      }
    }, [...LS_JWT_LEGACY_PAINEL_LIMPAR_E2E]);
  }

  await page.route("**/api/auth/login", async (route) => {
    if (route.request().method() !== "POST") {
      await route.continue();
      return;
    }
    const email = extrairEmailDoPost(route, "e2e@teste.com");
    await fulfillBffPainelJson(route, {
      tokenCookie: token,
      nome,
      email,
      perfil_conta: perfil,
      cookieMaxAgeSegundos,
    });
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
  const limparLs = opts.limparLocalStoragePainelAntesDeCadaDocumento ?? false;
  const cookieMaxAgeSegundos = opts.cookieMaxAgeSegundos;

  if (limparLs) {
    await page.addInitScript((keys: readonly string[]) => {
      try {
        for (const k of keys) window.localStorage.removeItem(k);
      } catch {
        /* storage indisponível */
      }
    }, [...LS_JWT_LEGACY_PAINEL_LIMPAR_E2E]);
  }

  await page.route("**/api/auth/cadastro", async (route) => {
    if (route.request().method() !== "POST") {
      await route.continue();
      return;
    }
    const { nome, email } = extrairNomeEmailCadastro(route, {
      nome: nomeDefault,
      email: "novo.e2e@teste.com",
    });
    await fulfillBffPainelJson(route, {
      tokenCookie: token,
      nome,
      email,
      perfil_conta: perfil,
      cookieMaxAgeSegundos,
    });
  });
}
