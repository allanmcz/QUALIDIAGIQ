import { defineConfig, devices } from "@playwright/test";

/** Porta fixa evita colisão com outro serviço no host (Next QDI usa :3010 por padrão). */
const e2ePort = process.env.PLAYWRIGHT_PORT ?? "3333";
const baseURL =
  process.env.PLAYWRIGHT_BASE_URL ?? `http://127.0.0.1:${e2ePort}`;

const skipServer = process.env.PLAYWRIGHT_SKIP_WEBSERVER === "1";

/** P8 — só specs que usam `test.describe.skip` quando ausente; servidor precisa do build-time flag. */
const wizardNormativaE2E = process.env.PLAYWRIGHT_WIZARD_NORMATIVA === "1";

/**
 * Gravação completa para avaliação (vídeo, trace, screenshot + relatório HTML).
 * Activar: ``PLAYWRIGHT_RECORD_EVAL=1`` (ex.: ``npm run test:e2e:record-eval``).
 */
const recordEval = process.env.PLAYWRIGHT_RECORD_EVAL === "1";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: !recordEval,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: recordEval ? 1 : process.env.CI ? 1 : undefined,
  reporter: recordEval
    ? [
        ["list"],
        [
          "html",
          { open: "never", outputFolder: "playwright-report-eval" },
        ],
      ]
    : "list",
  use: {
    baseURL,
    trace: recordEval ? "on" : "on-first-retry",
    video: recordEval ? "on" : "off",
    screenshot: recordEval ? "on" : "only-on-failure",
  },
  /** Fase 5 hardening — mobile só em `mobile-smoke.spec.ts` (viewport Pixel 5). */
  projects: [
    {
      name: "chromium-desktop",
      use: { ...devices["Desktop Chrome"] },
      testIgnore: "**/mobile-smoke.spec.ts",
    },
    {
      name: "chromium-mobile",
      use: { ...devices["Pixel 5"] },
      testMatch: "**/mobile-smoke.spec.ts",
    },
  ],
  webServer: skipServer
    ? undefined
    : {
        command: `npm run dev -- -p ${e2ePort}`,
        url: baseURL,
        /**
         * P8: `NEXT_PUBLIC_WIZARD_NORMATIVA` só entra no bundle ao subir o dev server.
         * Reutilizar um Next já na porta sem esse flag quebra `wizard-normativa.spec.ts`.
         */
        reuseExistingServer: process.env.CI
          ? false
          : !wizardNormativaE2E,
        timeout: 120_000,
        env: {
          ...process.env,
          /** Same-origin `/api-backend` + cookie BFF — alinhado a `frontend/.env.local.example`. */
          NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL ?? "/api-backend",
          /** Sem isto, o proxy `app/api-backend/...` não alcança a API e o painel falha em E2E. */
          API_PROXY_TARGET: process.env.API_PROXY_TARGET ?? "http://127.0.0.1:60000",
          ...(wizardNormativaE2E ? { NEXT_PUBLIC_WIZARD_NORMATIVA: "true" } : {}),
        },
      },
});
