import { defineConfig, devices } from "@playwright/test";

/** Porta fixa evita colisão com outro `next dev` comum em :3000 no host. */
const e2ePort = process.env.PLAYWRIGHT_PORT ?? "3333";
const baseURL =
  process.env.PLAYWRIGHT_BASE_URL ?? `http://127.0.0.1:${e2ePort}`;

const skipServer = process.env.PLAYWRIGHT_SKIP_WEBSERVER === "1";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: "list",
  use: {
    baseURL,
    trace: "on-first-retry",
    ...devices["Desktop Chrome"],
  },
  webServer: skipServer
    ? undefined
    : {
        command: `npm run dev -- -p ${e2ePort}`,
        url: baseURL,
        reuseExistingServer: false,
        timeout: 120_000,
      },
});
